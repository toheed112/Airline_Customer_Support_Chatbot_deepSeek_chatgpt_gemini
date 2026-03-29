# backend/tools/__init__.py - Updated exports for JSON system
"""
Tools package for Swiss Airlines chatbot.
All tools now use JSON database instead of SQLite.
"""

from .flights import search_flights, update_ticket_to_new_flight, book_flight
from .hotels import search_hotels, book_hotel
from .car_rentals import search_cars, book_car
from .excursions import search_excursions, book_excursion
from .policy import lookup_policy
from .utilities import fetch_user_info, search_web, get_passenger_bookings
from .booking_simulator import booking_sim

__all__ = [
    # Flight operations
    "search_flights",
    "update_ticket_to_new_flight",
    "book_flight",
    
    # Hotel operations
    "search_hotels",
    "book_hotel",
    
    # Car rental operations
    "search_cars",
    "book_car",
    
    # Excursion operations
    "search_excursions",
    "book_excursion",
    
    # Policy and utilities
    "lookup_policy",
    "fetch_user_info",
    "search_web",
    "get_passenger_bookings",
    
    # Booking simulator
    "booking_sim",
]
