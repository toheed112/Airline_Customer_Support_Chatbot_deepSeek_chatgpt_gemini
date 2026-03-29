import json
import os
from dotenv import load_dotenv   # ✅ added
from openai import OpenAI

# ✅ load .env
load_dotenv()

# Use existing OpenAI key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INTENT_SYSTEM_PROMPT = """
You are a travel assistant intent classifier.

Your job:
- Understand the user's request in natural language
- Decide the intent
- Extract relevant parameters

Allowed intents:
- flight_search
- hotel_search
- car_search
- excursion_search
- policy_query
- booking_action  ← use when user says "book it", "yes book", "confirm", "ok book a flight", "proceed with booking"
- passenger_id    ← use when user is providing their ID, e.g. "id 4", "my id is 123", "passenger id: ABC"
- unknown

Rules:
- Return ONLY valid JSON
- No explanations
- If unsure, use intent = "unknown"
- "booking" field = true only for booking_action intent

JSON format:
{
  "intent": "...",
  "parameters": { },
  "booking": true/false
}
"""

def classify_intent(user_message: str) -> dict:
    """
    Uses OpenAI to classify user intent and extract parameters.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # ✅ small safety fix (in case model adds extra text)
        start = content.find("{")
        end = content.rfind("}") + 1
        content = content[start:end]

        return json.loads(content)

    except Exception as e:
        print("Intent classifier error:", e)  # ✅ small debug help
        return {
            "intent": "unknown",
            "parameters": {},
            "booking": False
        }
