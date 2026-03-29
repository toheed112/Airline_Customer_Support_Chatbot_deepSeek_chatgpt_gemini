# backend/tools/utilities.py - Updated for JSON database
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from backend.database.json_handler import db

load_dotenv()

logger = logging.getLogger(__name__)

# Tavily API (optional)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
HAS_TAVILY = False

try:
    from tavily import TavilyClient
    if TAVILY_API_KEY:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        HAS_TAVILY = True
        logger.info("✅ Tavily client initialized")
except ImportError:
    logger.warning("Tavily not installed - web search disabled")
except Exception as e:
    logger.warning(f"Tavily initialization failed: {e}")


def fetch_user_info(passenger_id: str) -> str:
    """
    Fetch user information from JSON database.
    
    Args:
        passenger_id: Passenger ID
    
    Returns:
        Formatted user information string
    """
    if not passenger_id:
        return "No passenger ID provided - Guest mode"
    
    try:
        # Try to find user by multiple fields: passenger_id string, numeric id, or string id
        user = db.find_one('users', {'passenger_id': passenger_id})
        if not user:
            user = db.find_one('users', {'id': int(passenger_id)}) if passenger_id.isdigit() else None
        if not user:
            user = db.find_one('users', {'id': passenger_id})
        
        if not user:
            logger.info(f"User {passenger_id} not found in JSON database")
            return f"Passenger ID {passenger_id} (Guest - not in system)"
        
        # Get user's bookings
        bookings = db.query('bookings', {'user_id': passenger_id})
        
        # Format user info
        name = user.get('name', 'Unknown')
        
        info = f"""
**Passenger Information:**
- Name: {name}
- ID: {passenger_id}
- Status: Registered User

**Active Bookings:** {len(bookings)} booking(s)
"""
        
        if bookings:
            info += "\n**Recent Bookings:**\n"
            for booking in bookings[:3]:  # Show max 3
                ticket = booking.get('ticket_no', 'N/A')
                status = booking.get('status', 'UNKNOWN')
                route = f"{booking.get('src', '?')} → {booking.get('dst', '?')}"
                info += f"- {ticket}: {route} ({status})\n"
        
        logger.info(f"Fetched info for passenger {passenger_id}")
        return info.strip()
        
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        return f"Error retrieving user information: {str(e)}"


def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web for current information using Tavily.
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        Formatted search results or error message
    """
    if not HAS_TAVILY:
        logger.warning("Web search attempted but Tavily not available")
        return (
            "⚠️ Web search is currently unavailable. "
            "This is a prototype system with static data. "
            "For real-time information, please check airline websites directly."
        )
    
    try:
        logger.info(f"Searching web for: {query}")
        results = tavily_client.search(query=query, max_results=max_results)
        
        if not results or 'results' not in results or not results['results']:
            return f"No web results found for '{query}'"
        
        # Format results
        formatted = f"🔍 **Web Search Results for '{query}':**\n\n"
        
        for i, result in enumerate(results['results'][:max_results], 1):
            title = result.get('title', 'No title')
            content = result.get('content', 'No content')[:200]
            url = result.get('url', '')
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   {content}...\n"
            if url:
                formatted += f"   Source: {url}\n"
            formatted += "\n"
        
        logger.info(f"✅ Found {len(results['results'])} web results")
        return formatted.strip()
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"❌ Web search failed: {str(e)}"


def get_passenger_bookings(passenger_id: str) -> List[Dict[str, Any]] | str:
    """
    Get all bookings for a passenger from JSON database.
    
    Args:
        passenger_id: Passenger ID
    
    Returns:
        List of booking dictionaries or error message
    """
    if not passenger_id:
        return "Passenger ID required"
    
    try:
        # Search bookings by user_id string, or by resolving numeric id to passenger_id
        bookings = db.query('bookings', {'user_id': passenger_id})
        
        if not bookings:
            # Try resolving: if passenger_id is a number, look up their actual passenger_id string
            user = db.find_one('users', {'passenger_id': passenger_id})
            if not user and passenger_id.isdigit():
                user = db.find_one('users', {'id': int(passenger_id)})
            if user:
                actual_pid = user.get('passenger_id', str(user.get('id', passenger_id)))
                bookings = db.query('bookings', {'user_id': actual_pid})
        
        if not bookings:
            return f"No bookings found for passenger {passenger_id}"
        
        # Enrich bookings with flight details
        enriched_bookings = []
        for booking in bookings:
            route_id = booking.get('route_id') or booking.get('flight_id')
            if route_id:
                route = db.find_one('routes', {'id': route_id})
                if route:
                    booking['route_details'] = route
            
            enriched_bookings.append(booking)
        
        logger.info(f"Retrieved {len(enriched_bookings)} bookings for {passenger_id}")
        return enriched_bookings
        
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        return f"Error: {str(e)}"


def validate_passenger(passenger_id: str) -> bool:
    """
    Validate if passenger exists in JSON database.
    
    Args:
        passenger_id: Passenger ID to validate
    
    Returns:
        True if passenger exists, False otherwise
    """
    try:
        # Check by passenger_id string first, then numeric id
        user = db.find_one('users', {'passenger_id': passenger_id})
        if not user and passenger_id.isdigit():
            user = db.find_one('users', {'id': int(passenger_id)})
        if not user:
            user = db.find_one('users', {'id': passenger_id})
        
        return user is not None
        
    except Exception as e:
        logger.error(f"Error validating passenger: {e}")
        return False


def get_system_stats() -> Dict[str, Any]:
    """
    Get system statistics from JSON database.
    
    Returns:
        Dictionary with system stats
    """
    try:
        stats = {
            'total_airports': len(db.get_all('airports')),
            'total_airlines': len(db.get_all('airlines')),
            'total_routes': len(db.get_all('routes')),
            'total_users': len(db.get_all('users')),
            'total_bookings': len(db.get_all('bookings')),
            'active_bookings': len([b for b in db.get_all('bookings') if b.get('status') == 'CONFIRMED'])
        }
        
        logger.info("System stats retrieved from JSON")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {"error": str(e)}
