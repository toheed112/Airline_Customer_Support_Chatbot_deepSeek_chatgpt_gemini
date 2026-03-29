# backend/database/json_handler.py
"""
JSON-based data handler to replace SQLite.
Handles all data operations with JSON file backend.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

# Path to JSON data file
JSON_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "db_dump.json"

# Thread-safe write lock
_write_lock = Lock()


class JSONDatabase:
    """Thread-safe JSON database handler."""
    
    def __init__(self, data_path: Path = JSON_DATA_PATH):
        self.data_path = data_path
        self._cache = None
        self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            if not self.data_path.exists():
                logger.warning(f"JSON file not found: {self.data_path}")
                # Create empty structure
                empty_data = {
                    "airlines": [],
                    "airports": [],
                    "routes": [],
                    "bookings": [],
                    "users": [],
                    "hotels": [],
                    "cars": [],
                    "excursions": []
                }
                self._save_data(empty_data)
                return empty_data
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)
            
            logger.info(f"✓ Loaded JSON data: {len(self._cache)} collections")
            return self._cache
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.data_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            raise
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file (thread-safe)."""
        with _write_lock:
            try:
                # Ensure directory exists
                self.data_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write with pretty formatting
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self._cache = data
                logger.info("✓ Data saved to JSON")
                
            except Exception as e:
                logger.error(f"Error saving JSON: {e}")
                raise
    
    def get_all(self, collection: str) -> List[Dict[str, Any]]:
        """Get all records from a collection."""
        if self._cache is None:
            self._load_data()
        
        return self._cache.get(collection, [])
    
    def query(self, collection: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query collection with filters.
        
        Args:
            collection: Collection name (e.g., 'airports', 'routes')
            filters: Dict of field:value pairs for filtering
            limit: Maximum results
        
        Returns:
            List of matching records
        """
        records = self.get_all(collection)
        
        if not filters:
            return records[:limit]
        
        # Apply filters
        results = []
        for record in records:
            match = True
            for key, value in filters.items():
                # Support nested keys with dot notation
                if '.' in key:
                    parts = key.split('.')
                    record_value = record
                    for part in parts:
                        record_value = record_value.get(part, {})
                    if record_value != value:
                        match = False
                        break
                else:
                    # Case-insensitive string matching
                    if isinstance(value, str) and isinstance(record.get(key), str):
                        if value.lower() not in record.get(key, '').lower():
                            match = False
                            break
                    elif record.get(key) != value:
                        match = False
                        break
            
            if match:
                results.append(record)
                if len(results) >= limit:
                    break
        
        return results
    
    def find_one(self, collection: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single record matching filters."""
        results = self.query(collection, filters, limit=1)
        return results[0] if results else None
    
    def insert(self, collection: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert new record into collection."""
        data = self._cache.copy()
        
        if collection not in data:
            data[collection] = []
        
        # Add timestamp if not present
        if 'created_at' not in record:
            record['created_at'] = datetime.utcnow().isoformat()
        
        # Auto-increment ID for certain collections
        if 'id' not in record and collection in ['bookings', 'hotels', 'cars', 'excursions']:
            existing_ids = [r.get('id', 0) for r in data[collection]]
            record['id'] = max(existing_ids) + 1 if existing_ids else 1
        
        data[collection].append(record)
        self._save_data(data)
        
        logger.info(f"Inserted record into {collection}")
        return record
    
    def update(self, collection: str, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """
        Update records matching filters.
        
        Returns:
            Number of records updated
        """
        data = self._cache.copy()
        
        if collection not in data:
            return 0
        
        updated_count = 0
        for record in data[collection]:
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            
            if match:
                record.update(updates)
                record['updated_at'] = datetime.utcnow().isoformat()
                updated_count += 1
        
        if updated_count > 0:
            self._save_data(data)
            logger.info(f"Updated {updated_count} records in {collection}")
        
        return updated_count
    
    def delete(self, collection: str, filters: Dict[str, Any]) -> int:
        """
        Delete records matching filters.
        
        Returns:
            Number of records deleted
        """
        data = self._cache.copy()
        
        if collection not in data:
            return 0
        
        original_count = len(data[collection])
        
        # Keep only non-matching records
        data[collection] = [
            record for record in data[collection]
            if not all(record.get(k) == v for k, v in filters.items())
        ]
        
        deleted_count = original_count - len(data[collection])
        
        if deleted_count > 0:
            self._save_data(data)
            logger.info(f"Deleted {deleted_count} records from {collection}")
        
        return deleted_count
    
    def reload(self) -> None:
        """Force reload data from file."""
        self._load_data()


# Global instance
db = JSONDatabase()
