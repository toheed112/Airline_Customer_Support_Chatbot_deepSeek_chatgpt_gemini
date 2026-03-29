# ========================================
# backend/tools/excursions.py - Updated for JSON
# ========================================

from typing import List, Dict, Any
import logging
from backend.tools.booking_simulator import booking_sim

logger = logging.getLogger(__name__)


def search_excursions(location: str, limit=20) -> List[Dict[str, Any]] | str:
    """Search excursions (simulated)."""
    try:
        from backend.tools.location_parser import LocationParser
        parser = LocationParser()
        
        iata = parser.resolve_iata(location)
        if not iata:
            return f"❌ Unknown location: '{location}'."
        
        location_info = parser.get_location_info(iata)
        city = location_info['city'] if location_info else location
        
        # Mock excursion data
        mock_excursions = [
            {
                'id': 1,
                'name': f'{city} Old Town Walking Tour',
                'location': iata,
                'city': city,
                'description': 'Explore historic landmarks and hidden gems',
                'duration_hours': 3.0,
                'price': 45.0,
                'max_participants': 15,
                'available_slots': 10
            },
            {
                'id': 2,
                'name': f'{city} Food & Culture Experience',
                'location': iata,
                'city': city,
                'description': 'Taste local cuisine and learn about traditions',
                'duration_hours': 4.0,
                'price': 85.0,
                'max_participants': 20,
                'available_slots': 15
            },
            {
                'id': 3,
                'name': f'{city} Night Lights Tour',
                'location': iata,
                'city': city,
                'description': 'Evening tour of illuminated attractions',
                'duration_hours': 2.5,
                'price': 55.0,
                'max_participants': 30,
                'available_slots': 25
            }
        ]
        
        logger.info(f"Found {len(mock_excursions)} excursions in {city}")
        return mock_excursions[:limit]
        
    except Exception as e:
        logger.error(f"Error searching excursions: {e}")
        return f"Error: {str(e)}"


def book_excursion(excursion_id: int, passenger_id: str, date=None, num_participants=1) -> str:
    """Book an excursion using booking simulator."""
    if not passenger_id:
        raise ValueError("❌ Passenger ID required for booking.")
    
    result = booking_sim.book_excursion(excursion_id, passenger_id, date, num_participants)
    
    if result['success']:
        return result['message']
    else:
        raise ValueError(result.get('error', 'Booking failed'))
