# backend/tools/location_parser.py - UPDATED with JSON integration
import re
import logging
from typing import Optional, Dict
from difflib import get_close_matches

logger = logging.getLogger(__name__)

# Load airport data from JSON at runtime
_airport_cache = None

def _load_airports():
    """Load airports from JSON database."""
    global _airport_cache
    if _airport_cache is not None:
        return _airport_cache
    
    try:
        from backend.database.json_handler import db
        airports = db.get_all('airports')
        
        # Build lookup dictionary
        _airport_cache = {}
        for apt in airports:
            iata = apt.get('iata', '').upper()
            if iata and len(iata) == 3:
                _airport_cache[iata] = {
                    'city': apt.get('city', ''),
                    'country': apt.get('country', ''),
                    'name': apt.get('name', ''),
                    'iata': iata
                }
        
        logger.info(f"✓ Loaded {len(_airport_cache)} airports from JSON")
        return _airport_cache
        
    except Exception as e:
        logger.error(f"Failed to load airports: {e}")
        # Fallback to minimal set
        return {
            'ZRH': {'city': 'Zurich', 'country': 'Switzerland', 'name': 'Zurich Airport', 'iata': 'ZRH'},
            'JFK': {'city': 'New York', 'country': 'USA', 'name': 'JFK Airport', 'iata': 'JFK'},
            'LHR': {'city': 'London', 'country': 'UK', 'name': 'Heathrow', 'iata': 'LHR'},
        }


# City aliases for better matching
CITY_ALIASES = {
    'zurich': ['zürich', 'zurih', 'zuerich', 'zur'],
    'geneva': ['genève', 'genf', 'geneve'],
    'new york': ['nyc', 'ny', 'new york city', 'newyork', 'manhattan'],
    'london': ['lon'],
    'paris': ['par'],
    'frankfurt': ['frank'],
    'los angeles': ['la', 'los ang'],
    'san francisco': ['sf', 'san fran'],
}


class LocationParser:
    """Intelligent location parser with JSON database integration."""
    
    def __init__(self):
        self.airports = _load_airports()
        self._build_city_lookup()
    
    def _build_city_lookup(self):
        """Build reverse lookup: city -> IATA codes."""
        self.city_to_iata = {}
        
        for iata, info in self.airports.items():
            city_lower = info['city'].lower()
            
            if city_lower not in self.city_to_iata:
                self.city_to_iata[city_lower] = []
            self.city_to_iata[city_lower].append(iata)
            
            # Add aliases
            for alias_group, aliases in CITY_ALIASES.items():
                if city_lower in aliases or city_lower == alias_group:
                    for alias in aliases:
                        if alias not in self.city_to_iata:
                            self.city_to_iata[alias] = []
                        if iata not in self.city_to_iata[alias]:
                            self.city_to_iata[alias].append(iata)
    
    def normalize_iata(self, code: str) -> Optional[str]:
        """
        Normalize and validate IATA codes.
        
        FIXES:
        - No longer converts ZUR → ZRH
        - Uses actual airport data from JSON
        """
        if not code:
            return None
        
        # Clean and uppercase
        code = re.sub(r'[^A-Za-z]', '', code).upper()
        
        if len(code) != 3:
            return None
        
        # Direct match
        if code in self.airports:
            return code
        
        # Fuzzy match for typos
        matches = get_close_matches(code, self.airports.keys(), n=1, cutoff=0.8)
        return matches[0] if matches else None
    
    def resolve_iata(self, location: str) -> Optional[str]:
        """
        Resolve any location string to IATA code.
        
        Handles:
        - IATA codes (direct)
        - City names
        - City aliases
        - Fuzzy matching
        """
        location_clean = location.strip().lower()
        
        # Try as IATA code first
        iata = self.normalize_iata(location)
        if iata:
            return iata
        
        # Try exact city match
        if location_clean in self.city_to_iata:
            return self.city_to_iata[location_clean][0]
        
        # Fuzzy city match
        city_names = list(self.city_to_iata.keys())
        matches = get_close_matches(location_clean, city_names, n=1, cutoff=0.85)
        if matches:
            return self.city_to_iata[matches[0]][0]
        
        return None
    
    def parse_location(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extract departure and arrival from query.
        
        Returns:
            Dict with 'departure' and 'arrival' IATA codes
        """
        query_lower = query.lower()
        result = {'departure': None, 'arrival': None}
        
        # Pattern 1: "from X to Y"
        from_to = re.search(r'(?:from\s+)?(\w+(?:\s+\w+)?)\s+to\s+(\w+(?:\s+\w+)?)', query_lower)
        if from_to:
            result['departure'] = self.resolve_iata(from_to.group(1))
            result['arrival'] = self.resolve_iata(from_to.group(2))
            return result
        
        # Pattern 2: IATA codes in CAPS
        iata_codes = re.findall(r'\b([A-Z]{3})\b', query)
        if len(iata_codes) >= 2:
            result['departure'] = self.normalize_iata(iata_codes[0])
            result['arrival'] = self.normalize_iata(iata_codes[1])
            return result
        elif len(iata_codes) == 1:
            result['departure'] = self.normalize_iata(iata_codes[0])
            return result
        
        # Pattern 3: Keywords
        keywords = {
            'departure': ['from', 'leaving', 'departing', 'out of'],
            'arrival': ['to', 'arriving', 'destination', 'going to']
        }
        
        for key, words in keywords.items():
            for word in words:
                pattern = rf'{word}\s+(\w+(?:\s+\w+)?)'
                match = re.search(pattern, query_lower)
                if match:
                    result[key] = self.resolve_iata(match.group(1))
        
        # Pattern 4: Scan for known locations
        if not result['departure']:
            tokens = query_lower.split()
            for token in tokens:
                resolved = self.resolve_iata(token)
                if resolved:
                    result['departure'] = resolved
                    break
        
        return result
    
    def get_location_info(self, iata: str) -> Optional[Dict]:
        """Get full airport information."""
        return self.airports.get(iata)
    
    def format_location(self, iata: str) -> str:
        """Format: 'City (IATA)'."""
        info = self.airports.get(iata)
        if info:
            return f"{info['city']} ({iata})"
        return iata
    
    def reload(self):
        """Reload airport data from JSON."""
        global _airport_cache
        _airport_cache = None
        self.airports = _load_airports()
        self._build_city_lookup()
