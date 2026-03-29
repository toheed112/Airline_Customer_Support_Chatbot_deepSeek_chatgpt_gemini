# backend/tools/booking_simulator.py
"""
Realistic booking simulation for prototype demonstration.
Simulates the complete booking workflow without real payment processing.
"""

import logging
import random
from datetime import datetime
from typing import Dict, Any, Optional

from backend.database.json_handler import db

logger = logging.getLogger(__name__)


class BookingSimulator:
    """Simulates realistic booking processes for all services."""
    
    @staticmethod
    def generate_ticket_number(service_type: str, service_id: int) -> str:
        """Generate realistic ticket/confirmation numbers."""
        prefix_map = {
            'flight': 'FLT',
            'hotel': 'HTL',
            'car': 'CAR',
            'excursion': 'EXC'
        }
        prefix = prefix_map.get(service_type, 'SVC')
        timestamp = datetime.now().strftime('%Y%m%d')
        random_suffix = random.randint(1000, 9999)
        
        return f"{prefix}-{timestamp}-{service_id:04d}-{random_suffix}"
    
    @staticmethod
    def book_flight(
        flight_id: int,
        passenger_id: str,
        seat_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate flight booking with realistic flow.
        
        Steps:
        1. Validate flight availability
        2. Check passenger exists
        3. Generate ticket
        4. Create booking record
        5. Return confirmation
        """
        try:
            # Step 1: Get flight details
            route = db.find_one('routes', {'id': flight_id})
            if not route:
                return {
                    'success': False,
                    'error': f'Flight ID {flight_id} not found'
                }
            
            # Step 2: Validate passenger (check by passenger_id string OR numeric id)
            if passenger_id:
                user = db.find_one('users', {'passenger_id': passenger_id})
                if not user and passenger_id.isdigit():
                    user = db.find_one('users', {'id': int(passenger_id)})
                if not user:
                    logger.warning(f"Passenger {passenger_id} not found in system — proceeding as demo/guest")
                    canonical_pid = passenger_id
                else:
                    # Use the passenger_id string from the user record as canonical id
                    canonical_pid = user.get('passenger_id', str(user.get('id', passenger_id)))
                    logger.info(f"Passenger validated: {user.get('name', passenger_id)}")
            else:
                canonical_pid = passenger_id

            # Step 3: Generate booking details
            ticket_no = BookingSimulator.generate_ticket_number('flight', flight_id)
            
            # Simulate seat assignment
            if not seat_preference:
                row = random.randint(1, 35)
                seat = random.choice(['A', 'B', 'C', 'D', 'E', 'F'])
                seat_number = f"{row}{seat}"
            else:
                seat_number = seat_preference
            
            # Simulate pricing (base + random variance)
            base_price = route.get('price', 500.0)
            final_price = base_price * random.uniform(0.9, 1.3)
            
            # Step 4: Create booking record
            booking = {
                'ticket_no': ticket_no,
                'user_id': canonical_pid,
                'flight_id': flight_id,
                'route_id': route.get('id'),
                'src': route.get('src'),
                'dst': route.get('dst'),
                'airline': route.get('airline'),
                'status': 'CONFIRMED',
                'booking_date': datetime.utcnow().isoformat(),
                'price_paid': round(final_price, 2),
                'seat_number': seat_number,
                'check_in_status': 'NOT_CHECKED_IN'
            }
            
            db.insert('bookings', booking)
            
            logger.info(f"✅ Flight booked: {ticket_no}")
            
            # Step 5: Return confirmation
            airports = {apt['iata']: apt for apt in db.get_all('airports')}
            src_city = airports.get(route.get('src'), {}).get('city', route.get('src'))
            dst_city = airports.get(route.get('dst'), {}).get('city', route.get('dst'))
            
            return {
                'success': True,
                'ticket_no': ticket_no,
                'flight_no': f"{route.get('airline')}{route.get('id')}",
                'route': f"{src_city} ({route.get('src')}) → {dst_city} ({route.get('dst')})",
                'departure': route.get('src'),
                'arrival': route.get('dst'),
                'seat': seat_number,
                'price': round(final_price, 2),
                'status': 'CONFIRMED',
                'booking_date': booking['booking_date'],
                'message': f"🎉 Flight booked! Your ticket number is {ticket_no}. Seat {seat_number} confirmed."
            }
            
        except Exception as e:
            logger.error(f"Flight booking error: {e}")
            return {
                'success': False,
                'error': f'Booking failed: {str(e)}'
            }
    
    @staticmethod
    def book_hotel(
        hotel_id: int,
        passenger_id: str,
        checkin_date: Optional[str] = None,
        checkout_date: Optional[str] = None,
        num_guests: int = 1
    ) -> Dict[str, Any]:
        """Simulate hotel booking."""
        try:
            confirmation_no = BookingSimulator.generate_ticket_number('hotel', hotel_id)
            
            booking = {
                'confirmation_no': confirmation_no,
                'user_id': passenger_id,
                'hotel_id': hotel_id,
                'status': 'CONFIRMED',
                'checkin_date': checkin_date or 'TBD',
                'checkout_date': checkout_date or 'TBD',
                'num_guests': num_guests,
                'booking_date': datetime.utcnow().isoformat(),
                'price_paid': random.uniform(100, 500)
            }
            
            db.insert('hotel_bookings', booking)
            
            logger.info(f"✅ Hotel booked: {confirmation_no}")
            
            return {
                'success': True,
                'confirmation_no': confirmation_no,
                'hotel_id': hotel_id,
                'checkin': checkin_date or 'TBD',
                'checkout': checkout_date or 'TBD',
                'price': round(booking['price_paid'], 2),
                'message': f"🏨 Hotel reservation confirmed! Confirmation: {confirmation_no}"
            }
            
        except Exception as e:
            logger.error(f"Hotel booking error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def book_car(
        car_id: int,
        passenger_id: str,
        pickup_date: Optional[str] = None,
        dropoff_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate car rental booking."""
        try:
            confirmation_no = BookingSimulator.generate_ticket_number('car', car_id)
            
            booking = {
                'confirmation_no': confirmation_no,
                'user_id': passenger_id,
                'car_id': car_id,
                'status': 'CONFIRMED',
                'pickup_date': pickup_date or 'TBD',
                'dropoff_date': dropoff_date or 'TBD',
                'booking_date': datetime.utcnow().isoformat(),
                'price_paid': random.uniform(50, 200)
            }
            
            db.insert('car_bookings', booking)
            
            logger.info(f"✅ Car booked: {confirmation_no}")
            
            return {
                'success': True,
                'confirmation_no': confirmation_no,
                'car_id': car_id,
                'pickup': pickup_date or 'TBD',
                'dropoff': dropoff_date or 'TBD',
                'price': round(booking['price_paid'], 2),
                'message': f"🚗 Car rental confirmed! Confirmation: {confirmation_no}"
            }
            
        except Exception as e:
            logger.error(f"Car booking error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def book_excursion(
        excursion_id: int,
        passenger_id: str,
        date: Optional[str] = None,
        num_participants: int = 1
    ) -> Dict[str, Any]:
        """Simulate excursion booking."""
        try:
            confirmation_no = BookingSimulator.generate_ticket_number('excursion', excursion_id)
            
            booking = {
                'confirmation_no': confirmation_no,
                'user_id': passenger_id,
                'excursion_id': excursion_id,
                'status': 'CONFIRMED',
                'date': date or 'TBD',
                'num_participants': num_participants,
                'booking_date': datetime.utcnow().isoformat(),
                'price_paid': random.uniform(30, 150) * num_participants
            }
            
            db.insert('excursion_bookings', booking)
            
            logger.info(f"✅ Excursion booked: {confirmation_no}")
            
            return {
                'success': True,
                'confirmation_no': confirmation_no,
                'excursion_id': excursion_id,
                'date': date or 'TBD',
                'participants': num_participants,
                'price': round(booking['price_paid'], 2),
                'message': f"🎫 Excursion booked! Confirmation: {confirmation_no}"
            }
            
        except Exception as e:
            logger.error(f"Excursion booking error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_booking_details(ticket_no: str) -> Optional[Dict[str, Any]]:
        """Retrieve booking details by ticket/confirmation number."""
        try:
            # Search all booking collections
            collections = ['bookings', 'hotel_bookings', 'car_bookings', 'excursion_bookings']
            
            for collection in collections:
                booking = db.find_one(collection, {'ticket_no': ticket_no}) or \
                         db.find_one(collection, {'confirmation_no': ticket_no})
                if booking:
                    return booking
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving booking: {e}")
            return None
    
    @staticmethod
    def cancel_booking(ticket_no: str, passenger_id: str) -> Dict[str, Any]:
        """Simulate booking cancellation."""
        try:
            booking = BookingSimulator.get_booking_details(ticket_no)
            
            if not booking:
                return {
                    'success': False,
                    'error': f'Booking {ticket_no} not found'
                }
            
            # Verify ownership
            if booking.get('user_id') != passenger_id:
                return {
                    'success': False,
                    'error': 'Booking does not belong to this passenger'
                }
            
            # Update status
            for collection in ['bookings', 'hotel_bookings', 'car_bookings', 'excursion_bookings']:
                updated = db.update(
                    collection,
                    {'ticket_no': ticket_no},
                    {'status': 'CANCELLED', 'cancelled_at': datetime.utcnow().isoformat()}
                ) or db.update(
                    collection,
                    {'confirmation_no': ticket_no},
                    {'status': 'CANCELLED', 'cancelled_at': datetime.utcnow().isoformat()}
                )
                
                if updated > 0:
                    logger.info(f"✅ Booking {ticket_no} cancelled")
                    return {
                        'success': True,
                        'ticket_no': ticket_no,
                        'message': f'Booking {ticket_no} has been cancelled. Refund will be processed within 5-7 business days.'
                    }
            
            return {
                'success': False,
                'error': 'Cancellation failed'
            }
            
        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            return {'success': False, 'error': str(e)}


# Global instance
booking_sim = BookingSimulator()
