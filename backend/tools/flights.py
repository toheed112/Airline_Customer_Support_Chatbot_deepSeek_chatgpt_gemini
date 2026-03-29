# backend/tools/flights.py - Updated for JSON database
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from backend.database.json_handler import db
from backend.tools.location_parser import LocationParser

logger = logging.getLogger(__name__)

location_parser = LocationParser()


def search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    departure_date: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]] | str:
    """
    Search available flights from JSON database.
    
    Args:
        departure_airport: Departure airport (IATA, city, or alias)
        arrival_airport: Arrival airport (IATA, city, or alias)
        departure_date: Departure date (ISO or 'today'/'tomorrow')
        limit: Maximum results
    
    Returns:
        List of flight dictionaries or error message
    """
    try:
        # ==================== LOCATION NORMALIZATION ====================
        if departure_airport:
            normalized_dep = location_parser.resolve_iata(departure_airport)
            if normalized_dep:
                departure_airport = normalized_dep
                logger.info(f"Departure: {departure_airport}")
            else:
                return f"❌ Unknown departure: '{departure_airport}'. Try IATA codes (ZRH, JFK, LHR)."
        
        if arrival_airport:
            normalized_arr = location_parser.resolve_iata(arrival_airport)
            if normalized_arr:
                arrival_airport = normalized_arr
                logger.info(f"Arrival: {arrival_airport}")
            else:
                return f"❌ Unknown arrival: '{arrival_airport}'. Try IATA codes (ZRH, JFK, LHR)."
        
        # ==================== DATE HANDLING ====================
        date_filter = None
        if departure_date:
            if departure_date.lower() == "today":
                date_filter = datetime.now().date().isoformat()
            elif departure_date.lower() == "tomorrow":
                date_filter = (datetime.now().date() + timedelta(days=1)).isoformat()
            else:
                date_filter = departure_date
        
        # ==================== QUERY JSON DATABASE ====================
        all_routes = db.get_all('routes')
        airports = {apt['iata']: apt for apt in db.get_all('airports')}
        airlines = {airl['iata']: airl for airl in db.get_all('airlines')}
        
        # Filter routes
        results = []
        for route in all_routes:
            # Match departure
            if departure_airport and route.get('src') != departure_airport:
                continue
            
            # Match arrival
            if arrival_airport and route.get('dst') != arrival_airport:
                continue
            
            # Enrich route with airport/airline info
            src_info = airports.get(route.get('src'), {})
            dst_info = airports.get(route.get('dst'), {})
            airline_info = airlines.get(route.get('airline'), {})
            
            flight = {
                'id': route.get('id'),
                'flight_no': f"{route.get('airline', 'XX')}{route.get('id', '000')}",
                'airline': airline_info.get('name', route.get('airline')),
                'departure_airport': route.get('src'),
                'departure_city': src_info.get('city', ''),
                'departure_country': src_info.get('country', ''),
                'arrival_airport': route.get('dst'),
                'arrival_city': dst_info.get('city', ''),
                'arrival_country': dst_info.get('country', ''),
                'aircraft': route.get('equipment', 'Unknown'),
                'price': route.get('price', 500.0),
                'available': True
            }
            
            results.append(flight)
            
            if len(results) >= limit:
                break
        
        # ==================== RESULTS ====================
        if not results:
            msg = "No flights found"
            if departure_airport or arrival_airport:
                route = f" from {departure_airport or 'anywhere'} to {arrival_airport or 'anywhere'}"
                msg += route
            msg += ". Try different airports or routes."
            logger.info(msg)
            return msg
        
        logger.info(f"✅ Found {len(results)} flights")
        return results
        
    except Exception as e:
        logger.error(f"Error in search_flights: {e}")
        return f"Error searching flights: {str(e)}"


def get_flight_details(flight_id: int) -> Dict[str, Any] | str:
    """Get detailed flight information."""
    try:
        route = db.find_one('routes', {'id': flight_id})
        
        if not route:
            return f"Flight ID {flight_id} not found."
        
        # Enrich with airport info
        airports = {apt['iata']: apt for apt in db.get_all('airports')}
        airlines = {airl['iata']: airl for airl in db.get_all('airlines')}
        
        src_info = airports.get(route.get('src'), {})
        dst_info = airports.get(route.get('dst'), {})
        airline_info = airlines.get(route.get('airline'), {})
        
        flight = {
            'id': route.get('id'),
            'flight_no': f"{route.get('airline', 'XX')}{route.get('id', '000')}",
            'airline': airline_info.get('name', route.get('airline')),
            'departure_airport': route.get('src'),
            'departure_city': src_info.get('city', ''),
            'arrival_airport': route.get('dst'),
            'arrival_city': dst_info.get('city', ''),
            'aircraft': route.get('equipment', 'Unknown'),
            'price': route.get('price', 500.0)
        }
        
        logger.info(f"Retrieved flight {flight['flight_no']}")
        return flight
        
    except Exception as e:
        logger.error(f"Error getting flight details: {e}")
        return f"Error: {str(e)}"


def update_ticket_to_new_flight(
    ticket_no: str,
    new_flight_id: int,
    passenger_id: str
) -> str:
    """
    Update ticket to new flight (SIMULATED).
    
    In prototype mode, this simulates the booking update process.
    """
    if not passenger_id:
        logger.error("Ticket update without passenger ID")
        raise ValueError("❌ Passenger ID required for ticket changes.")
    
    if not ticket_no:
        raise ValueError("❌ Ticket number required.")
    
    if not new_flight_id:
        raise ValueError("❌ New flight ID required.")
    
    try:
        # Check if booking exists
        booking = db.find_one('bookings', {'ticket_no': ticket_no})
        
        if not booking:
            # SIMULATION: Create booking record
            logger.info(f"SIMULATION: Creating new booking for {ticket_no}")
            new_booking = {
                'ticket_no': ticket_no,
                'user_id': passenger_id,
                'flight_id': new_flight_id,
                'status': 'CONFIRMED',
                'booking_date': datetime.utcnow().isoformat()
            }
            db.insert('bookings', new_booking)
            return f"✅ Ticket {ticket_no} created and assigned to flight {new_flight_id}."
        
        # Update existing booking
        updates = {
            'flight_id': new_flight_id,
            'updated_at': datetime.utcnow().isoformat(),
            'status': 'MODIFIED'
        }
        db.update('bookings', {'ticket_no': ticket_no}, updates)
        
        logger.info(f"✅ Ticket {ticket_no} updated to flight {new_flight_id}")
        return f"✅ Ticket {ticket_no} successfully updated to flight {new_flight_id}."
        
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        return f"Error: {str(e)}"


def book_flight(flight_id: int, passenger_id: str) -> Dict[str, Any]:
    """
    Book a flight (SIMULATED BOOKING).
    
    Returns:
        Booking confirmation dict
    """
    if not passenger_id:
        raise ValueError("❌ Passenger ID required for booking.")
    
    try:
        # Resolve canonical passenger_id (handle "4" → "000543216", or keep as-is for guests)
        user = db.find_one('users', {'passenger_id': passenger_id})
        if not user and passenger_id.isdigit():
            user = db.find_one('users', {'id': int(passenger_id)})
        canonical_pid = user.get('passenger_id', str(user.get('id', passenger_id))) if user else passenger_id

        # Get flight details
        flight = get_flight_details(flight_id)
        
        if isinstance(flight, str):
            return {'error': flight}
        
        # Generate ticket number
        import random
        ticket_no = f"TKT-{flight['flight_no']}-{random.randint(1000, 9999)}"
        
        # Create booking
        booking = {
            'ticket_no': ticket_no,
            'user_id': canonical_pid,
            'flight_id': flight_id,
            'status': 'CONFIRMED',
            'price_paid': flight.get('price', 500.0),
            'booking_date': datetime.utcnow().isoformat(),
            'seat_number': f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
        }
        
        db.insert('bookings', booking)
        
        logger.info(f"✅ Flight booked: {ticket_no}")
        
        passenger_name = user.get('name', canonical_pid) if user else canonical_pid
        return {
            'success': True,
            'ticket_no': ticket_no,
            'flight_no': flight['flight_no'],
            'route': f"{flight['departure_city']} → {flight['arrival_city']}",
            'price': booking['price_paid'],
            'seat': booking['seat_number'],
            'passenger': passenger_name,
            'message': f"🎉 Booking confirmed! Ticket: {ticket_no}"
        }
        
    except Exception as e:
        logger.error(f"Booking error: {e}")
        return {'error': str(e)}
