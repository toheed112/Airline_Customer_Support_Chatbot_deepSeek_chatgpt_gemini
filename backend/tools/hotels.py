# backend/tools/hotels.py - Updated for JSON
import logging
from typing import List, Dict, Any
from backend.database.json_handler import db
from backend.tools.booking_simulator import booking_sim

logger = logging.getLogger(__name__)


def search_hotels(location: str, checkin=None, checkout=None, limit=20) -> List[Dict[str, Any]] | str:
    """Search hotels (simulated - returns mock data)."""
    try:
        from backend.tools.location_parser import LocationParser
        parser = LocationParser()
        
        # Resolve location to IATA code
        iata = parser.resolve_iata(location)
        if not iata:
            return f"❌ Unknown location: '{location}'. Try using city names or IATA codes."
        
        location_info = parser.get_location_info(iata)
        city = location_info['city'] if location_info else location
        
        # Mock hotel data
        mock_hotels = [
            {
                'id': 1,
                'name': f'Grand Hotel {city}',
                'location': iata,
                'city': city,
                'star_rating': 5,
                'price_per_night': 250.0,
                'rooms_available': 8,
                'amenities': ['WiFi', 'Spa', 'Restaurant', 'Pool', 'Gym']
            },
            {
                'id': 2,
                'name': f'City Inn {city}',
                'location': iata,
                'city': city,
                'star_rating': 3,
                'price_per_night': 120.0,
                'rooms_available': 15,
                'amenities': ['WiFi', 'Breakfast', 'Parking']
            },
            {
                'id': 3,
                'name': f'Budget Stay {city}',
                'location': iata,
                'city': city,
                'star_rating': 2,
                'price_per_night': 75.0,
                'rooms_available': 20,
                'amenities': ['WiFi', 'Breakfast']
            }
        ]
        
        logger.info(f"Found {len(mock_hotels)} hotels in {city}")
        return mock_hotels[:limit]
        
    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        return f"Error: {str(e)}"


def book_hotel(hotel_id: int, passenger_id: str, checkin=None, checkout=None) -> str:
    """Book a hotel using booking simulator."""
    if not passenger_id:
        raise ValueError("❌ Passenger ID required for booking.")
    
    result = booking_sim.book_hotel(hotel_id, passenger_id, checkin, checkout)
    
    if result['success']:
        return result['message']
    else:
        raise ValueError(result.get('error', 'Booking failed'))
