import sqlite3
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from contextlib import contextmanager
from pathlib import Path
from core.config import settings

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository with CRUD operations and connection management"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.DATABASE_URL.replace("sqlite:///", ""))
        self._setup_database()

    def _setup_database(self):
        """Ensure database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with proper row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False,
                      fetch_all: bool = True) -> Optional[Union[Dict, List[Dict]]]:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                return [dict(row) for row in cursor.fetchall()]
            return None

    def _execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an update/insert/delete query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    @abstractmethod
    def create_table(self) -> None:
        """Create the table for this repository"""
        pass

    @abstractmethod
    def create(self, entity: T) -> str:
        """Create a new entity and return its ID"""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get an entity by its ID"""
        pass

    @abstractmethod
    def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update an entity"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity"""
        pass

    @abstractmethod
    def list_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """List all entities with optional pagination"""
        pass

    def count(self) -> int:
        """Count all entities"""
        raise NotImplementedError("Count method must be implemented by subclass")

    def exists(self, entity_id: str) -> bool:
        """Check if an entity exists"""
        return self.get_by_id(entity_id) is not None