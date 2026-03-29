from __future__ import annotations

import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
import ollama

from backend.agents.intent_classifier import classify_intent
from backend.tools.location_parser import LocationParser
from backend.tools import (
    lookup_policy,
    search_flights,
    search_hotels,
    search_cars,
    search_excursions,
    search_web,
    fetch_user_info,
    book_flight,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")

# Initialize location parser
location_parser = LocationParser()


def agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Improved primary assistant (LLM-first + location-aware).

    - OpenAI decides intent (NO keyword routing)
    - LocationParser resolves cities / IATA codes
    - Guest users can explore
    - Passenger ID required for bookings (future)
    - DeepSeek generates final response
    """
    messages: List[Dict[str, Any]] = state.get("messages", [])
    passenger_id: str | None = state.get("passenger_id")
    user_info: str | None = state.get("user_info")

    if not messages:
        raise ValueError("State contains no messages")

    *history, last_msg = messages
    user_query = last_msg.get("content", "").strip()

    logger.info(f"Processing query: {user_query[:100]}")

    # ==================== EXTRACT PASSENGER ID FROM CHAT ====================
    import re
    id_just_provided = False

    # Match: 'id 42', 'my id is TEST', 'passenger id: 42'
    id_match = re.search(
        r'(?:passenger[\s_]*id|my[\s_]*id|id[\s_]*is|id)[\s:=#]*([A-Za-z0-9]+)',
        user_query, re.IGNORECASE
    )
    # Also match bare value like '42' or 'TEST001' on its own
    if not id_match:
        bare = re.fullmatch(r'\s*([A-Za-z0-9]{1,20})\s*', user_query)
        if bare and not re.fullmatch(
            r'(?:yes|no|ok|okay|sure|book|hi|hello|help|thanks|bye)',
            bare.group(1), re.IGNORECASE
        ):
            id_match = bare

    if id_match:
        extracted_id = id_match.group(1).strip()
        logger.info(f"Extracted passenger ID from message: {extracted_id}")
        passenger_id = extracted_id
        state["passenger_id"] = extracted_id
        id_just_provided = True

        from backend.database.json_handler import db as _db
        existing = _db.find_one('users', {'passenger_id': extracted_id})
        if not existing and extracted_id.isdigit():
            existing = _db.find_one('users', {'id': int(extracted_id)})
        if not existing:
            _db.insert('users', {
                'name': f'Passenger {extracted_id}',
                'passenger_id': extracted_id,
                'email': f'{extracted_id}@demo.com',
                'registered': 'chat'
            })
            logger.info(f"Auto-registered new passenger: {extracted_id}")

    # ==================== AUTO-BOOK IF ID JUST PROVIDED ====================
    # If user just gave their ID and we have a pending flight, book it now
    if id_just_provided and state.get('last_flight_id'):
        from backend.tools.flights import book_flight as _book_flight
        booking = _book_flight(int(state['last_flight_id']), passenger_id)
        if isinstance(booking, dict) and booking.get('success'):
            state['last_booking'] = booking
            confirmation = (
                f"Booking confirmed! Here are your details:\n\n"
                f"Ticket: {booking['ticket_no']}\n"
                f"Route: {booking['route']}\n"
                f"Seat: {booking['seat']}\n"
                f"Price: ${booking['price']:.2f}\n"
                f"Passenger ID: {passenger_id}\n\n"
                f"Your booking has been saved. Safe travels!"
            )
            messages.append({'role': 'assistant', 'content': confirmation})
            state['messages'] = messages
            return state

    # ==================== INTENT CLASSIFICATION (LLM-FIRST) ====================
    intent_data = classify_intent(user_query)

    intent = intent_data.get("intent", "unknown")
    params = intent_data.get("parameters", {})
    is_booking = intent_data.get("booking", False)

    logger.info(f"Detected intent: {intent}, booking={is_booking}")

    # ==================== LOCATION PARSING ====================
    locations = location_parser.parse_location(user_query)
    departure_iata = locations.get("departure")
    arrival_iata = locations.get("arrival")

    location_context = ""
    if departure_iata:
        location_context += f"Departure: {location_parser.format_location(departure_iata)}\n"
    if arrival_iata:
        location_context += f"Arrival: {location_parser.format_location(arrival_iata)}\n"

    # ==================== TOOL EXECUTION ====================
    tool_results: Dict[str, Any] = {}

    # If user is trying to book but still has no ID, ask for it (don't hard-block)
    if is_booking and not passenger_id:
        tool_results["info"] = (
            "To complete your booking I just need your Passenger ID. "
            "You can use any ID — for example type: id 12345\n\n"
            "You can also use a demo ID: 1, 2, or 3 (existing users) "
            "or any new ID you'd like and I'll register you automatically."
        )
    else:
        try:
            if intent == "flight_search":
                search_args = {}
                if departure_iata:
                    search_args["departure_airport"] = departure_iata
                if arrival_iata:
                    search_args["arrival_airport"] = arrival_iata
                if params.get("date"):
                    search_args["departure_date"] = params["date"]

                tool_results["flights"] = search_flights(**search_args)
                # Remember first flight ID so user can say "book it" next
                flights = tool_results["flights"]
                if isinstance(flights, list) and flights:
                    state["last_flight_id"] = flights[0].get("id")

            elif intent == "hotel_search":
                search_location = arrival_iata or departure_iata or params.get("location")
                if search_location:
                    tool_results["hotels"] = search_hotels(location=search_location)
                else:
                    tool_results["hotels"] = "Please specify a city or airport for hotel search."

            elif intent == "car_search":
                search_location = arrival_iata or departure_iata or params.get("location")
                if search_location:
                    tool_results["cars"] = search_cars(location=search_location)
                else:
                    tool_results["cars"] = "Please specify a location for car rental."

            elif intent == "excursion_search":
                search_location = arrival_iata or departure_iata or params.get("location")
                if search_location:
                    tool_results["excursions"] = search_excursions(location=search_location)
                else:
                    tool_results["excursions"] = "Please specify a destination."

            elif intent == "policy_query":
                tool_results["policy"] = lookup_policy(user_query)

            elif intent == "booking_action":
                # Attempt actual booking — passenger_id is guaranteed here
                flight_id = params.get("flight_id") or state.get("last_flight_id")
                if flight_id:
                    booking = book_flight(int(flight_id), passenger_id)
                    tool_results["booking"] = booking
                    if isinstance(booking, dict) and booking.get("success"):
                        state["last_booking"] = booking
                else:
                    # No flight ID in context — search first then ask
                    search_args = {}
                    if departure_iata:
                        search_args["departure_airport"] = departure_iata
                    if arrival_iata:
                        search_args["arrival_airport"] = arrival_iata
                    flights = search_flights(**search_args) if search_args else []
                    tool_results["flights"] = flights
                    tool_results["booking_prompt"] = (
                        "Please confirm which flight you'd like to book "
                        "by specifying the flight ID."
                    )

            elif intent == "unknown":
                tool_results["fallback"] = {
                    "message": (
                        "I can help you explore flights, hotels, car rentals, "
                        "excursions, and airline policies."
                    ),
                    "examples": [
                        "Flights from Zurich to New York",
                        "Hotels in Paris",
                        "Rent a car at JFK",
                        "Things to do in Zurich",
                        "What is the baggage allowance?"
                    ]
                }

            # Always attach user info if available
            if passenger_id:
                tool_results["user_info"] = fetch_user_info(passenger_id)

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            tool_results["error"] = f"Error retrieving information: {str(e)}"

    # ==================== PROMPT FOR DEEPSEEK ====================
    recent_history = history[-6:] if len(history) > 6 else history

    prompt = f"""You are a Swiss Airlines virtual assistant.

Current UTC time: {datetime.utcnow().isoformat()}Z

Parsed locations:
{location_context or "No specific locations detected"}

Recent conversation:
{json.dumps(recent_history[-3:], indent=2) if recent_history else "No previous messages"}

User question:
{user_query}

Trusted system data:
{json.dumps(tool_results, indent=2, default=str)}

INSTRUCTIONS:
- Use ONLY the data provided above
- Do NOT invent flights, prices, or availability
- Clearly explain if booking is blocked (guest mode)
- Be professional, friendly, and concise
- Show city names with IATA codes when relevant

Provide a helpful response:"""

    # ==================== RESPONSE GENERATION ====================
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7, "num_predict": 500}
        )
        answer = response["message"]["content"].strip()

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        answer = (
            "I’m having trouble generating a response right now, "
            "but I’ve gathered the available information above."
        )

    # ==================== UPDATE STATE ====================
    messages.append({"role": "assistant", "content": answer})
    state["messages"] = messages

    logger.info("Agent processing complete")
    return state
