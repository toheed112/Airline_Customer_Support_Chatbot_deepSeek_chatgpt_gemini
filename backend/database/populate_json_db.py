# backend/database/populate_json_db.py
"""
Populate the JSON database with rich demo data.
This replaces the SQLite populate script.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

JSON_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "db_dump.json"


def create_enhanced_json_database():
    """Create comprehensive JSON database with all necessary data."""
    
    print("🔧 Creating enhanced JSON database...")
    
    # ==================== AIRLINES ====================
    airlines = [
        {"iata": "LX", "name": "Swiss International Air Lines"},
        {"iata": "AA", "name": "American Airlines"},
        {"iata": "BA", "name": "British Airways"},
        {"iata": "AF", "name": "Air France"},
        {"iata": "LH", "name": "Lufthansa"},
        {"iata": "UA", "name": "United Airlines"},
    ]
    
    # ==================== AIRPORTS ====================
    airports = [
        # Switzerland
        {"iata": "ZRH", "city": "Zurich", "country": "Switzerland", "name": "Zurich Airport"},
        {"iata": "GVA", "city": "Geneva", "country": "Switzerland", "name": "Geneva Airport"},
        {"iata": "BSL", "city": "Basel", "country": "Switzerland", "name": "EuroAirport Basel"},
        
        # Europe
        {"iata": "LHR", "city": "London", "country": "UK", "name": "Heathrow Airport"},
        {"iata": "LGW", "city": "London", "country": "UK", "name": "Gatwick Airport"},
        {"iata": "CDG", "city": "Paris", "country": "France", "name": "Charles de Gaulle"},
        {"iata": "FRA", "city": "Frankfurt", "country": "Germany", "name": "Frankfurt Airport"},
        {"iata": "MUC", "city": "Munich", "country": "Germany", "name": "Munich Airport"},
        {"iata": "FCO", "city": "Rome", "country": "Italy", "name": "Fiumicino Airport"},
        {"iata": "AMS", "city": "Amsterdam", "country": "Netherlands", "name": "Schiphol Airport"},
        {"iata": "MAD", "city": "Madrid", "country": "Spain", "name": "Adolfo Suárez Madrid–Barajas"},
        {"iata": "BCN", "city": "Barcelona", "country": "Spain", "name": "Barcelona–El Prat"},
        
        # North America
        {"iata": "JFK", "city": "New York", "country": "USA", "name": "John F. Kennedy International"},
        {"iata": "EWR", "city": "Newark", "country": "USA", "name": "Newark Liberty International"},
        {"iata": "LGA", "city": "New York", "country": "USA", "name": "LaGuardia Airport"},
        {"iata": "ORD", "city": "Chicago", "country": "USA", "name": "O'Hare International"},
        {"iata": "LAX", "city": "Los Angeles", "country": "USA", "name": "Los Angeles International"},
        {"iata": "SFO", "city": "San Francisco", "country": "USA", "name": "San Francisco International"},
        {"iata": "MIA", "city": "Miami", "country": "USA", "name": "Miami International"},
        {"iata": "YYZ", "city": "Toronto", "country": "Canada", "name": "Toronto Pearson International"},
        
        # Asia & Middle East
        {"iata": "HKG", "city": "Hong Kong", "country": "Hong Kong", "name": "Hong Kong International"},
        {"iata": "SIN", "city": "Singapore", "country": "Singapore", "name": "Singapore Changi"},
        {"iata": "NRT", "city": "Tokyo", "country": "Japan", "name": "Narita International"},
        {"iata": "DXB", "city": "Dubai", "country": "UAE", "name": "Dubai International"},
    ]
    
    # ==================== ROUTES ====================
    routes = []
    route_id = 1
    
    # Popular routes from ZRH
    zrh_routes = [
        ("ZRH", "JFK", "LX", "A330", 850.0),
        ("ZRH", "LHR", "LX", "A320", 280.0),
        ("ZRH", "CDG", "LX", "A320", 250.0),
        ("ZRH", "FRA", "LX", "A220", 180.0),
        ("ZRH", "AMS", "LX", "A320", 220.0),
        ("ZRH", "FCO", "LX", "A321", 320.0),
        ("ZRH", "BCN", "LX", "A320", 300.0),
        ("ZRH", "LAX", "LX", "A340", 950.0),
        ("ZRH", "SFO", "LX", "A340", 980.0),
        ("ZRH", "ORD", "LX", "A330", 880.0),
        ("ZRH", "SIN", "LX", "A340", 1200.0),
        ("ZRH", "HKG", "LX", "A340", 1150.0),
    ]
    
    # Return routes (from destinations back to ZRH)
    for src, dst, airline, aircraft, price in zrh_routes:
        # Outbound
        routes.append({
            "id": route_id,
            "src": src,
            "dst": dst,
            "airline": airline,
            "equipment": aircraft,
            "price": price,
            "stops": 0
        })
        route_id += 1
        
        # Return
        routes.append({
            "id": route_id,
            "src": dst,
            "dst": src,
            "airline": airline,
            "equipment": aircraft,
            "price": price + 50,  # Slightly higher return price
            "stops": 0
        })
        route_id += 1
    
    # Add some GVA routes
    gva_routes = [
        ("GVA", "LHR", "LX", "A320", 290.0),
        ("GVA", "CDG", "LX", "A220", 200.0),
        ("GVA", "JFK", "LX", "A330", 900.0),
    ]
    
    for src, dst, airline, aircraft, price in gva_routes:
        routes.append({
            "id": route_id,
            "src": src,
            "dst": dst,
            "airline": airline,
            "equipment": aircraft,
            "price": price,
            "stops": 0
        })
        route_id += 1
        
        # Return
        routes.append({
            "id": route_id,
            "src": dst,
            "dst": src,
            "airline": airline,
            "equipment": aircraft,
            "price": price + 50,
            "stops": 0
        })
        route_id += 1
    
    # ==================== USERS ====================
    users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "passenger_id": "000543216"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "passenger_id": "000543217"
        },
        {
            "id": 3,
            "name": "Test User",
            "email": "test@example.com",
            "passenger_id": "TEST001"
        }
    ]
    
    # ==================== BOOKINGS ====================
    bookings = [
        {
            "id": 1,
            "ticket_no": "TKT-LX001-1234",
            "user_id": "000543216",
            "route_id": 1,
            "src": "ZRH",
            "dst": "JFK",
            "airline": "LX",
            "status": "CONFIRMED",
            "booking_date": datetime.utcnow().isoformat(),
            "price_paid": 850.0,
            "seat_number": "12A"
        },
        {
            "id": 2,
            "ticket_no": "TKT-LX002-5678",
            "user_id": "000543217",
            "route_id": 3,
            "src": "ZRH",
            "dst": "CDG",
            "airline": "LX",
            "status": "CONFIRMED",
            "booking_date": datetime.utcnow().isoformat(),
            "price_paid": 250.0,
            "seat_number": "15C"
        }
    ]
    
    # ==================== ASSEMBLE DATABASE ====================
    database = {
        "airlines": airlines,
        "airports": airports,
        "routes": routes,
        "users": users,
        "bookings": bookings,
        "hotel_bookings": [],
        "car_bookings": [],
        "excursion_bookings": []
    }
    
    # ==================== SAVE TO FILE ====================
    JSON_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(JSON_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON database created: {JSON_DATA_PATH}")
    print(f"   - {len(airlines)} airlines")
    print(f"   - {len(airports)} airports")
    print(f"   - {len(routes)} routes")
    print(f"   - {len(users)} users")
    print(f"   - {len(bookings)} bookings")
    
    return JSON_DATA_PATH


if __name__ == '__main__':
    create_enhanced_json_database()
