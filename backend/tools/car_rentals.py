# ========================================
# backend/tools/car_rentals.py - Updated for JSON
# ========================================

from typing import List, Dict, Any
import logging
from backend.tools.booking_simulator import booking_sim

logger = logging.getLogger(__name__)


def search_cars(location: str, dates=None, limit=20) -> List[Dict[str, Any]] | str:
    """Search rental cars (simulated)."""
    try:
        from backend.tools.location_parser import LocationParser
        parser = LocationParser()
        
        iata = parser.resolve_iata(location)
        if not iata:
            return f"❌ Unknown location: '{location}'."
        
        location_info = parser.get_location_info(iata)
        city = location_info['city'] if location_info else location
        
        # Mock car data
        mock_cars = [
            {
                'id': 1,
                'model': 'VW Golf',
                'category': 'Economy',
                'location': iata,
                'city': city,
                'price_per_day': 45.0,
                'available': 5,
                'features': ['Manual', 'AC', '4 seats']
            },
            {
                'id': 2,
                'model': 'BMW 3 Series',
                'category': 'Luxury',
                'location': iata,
                'city': city,
                'price_per_day': 120.0,
                'available': 2,
                'features': ['Automatic', 'AC', 'GPS', '5 seats']
            },
            {
                'id': 3,
                'model': 'Tesla Model 3',
                'category': 'Premium Electric',
                'location': iata,
                'city': city,
                'price_per_day': 150.0,
                'available': 3,
                'features': ['Electric', 'Automatic', 'GPS', '5 seats']
            }
        ]
        
        logger.info(f"Found {len(mock_cars)} cars in {city}")
        return mock_cars[:limit]
        
    except Exception as e:
        logger.error(f"Error searching cars: {e}")
        return f"Error: {str(e)}"


def book_car(car_id: int, passenger_id: str, pickup_date=None, dropoff_date=None) -> str:
    """Book a car using booking simulator."""
    if not passenger_id:
        raise ValueError("❌ Passenger ID required for booking.")
    
    result = booking_sim.book_car(car_id, passenger_id, pickup_date, dropoff_date)
    
    if result['success']:
        return result['message']
    else:
        raise ValueError(result.get('error', 'Booking failed'))
