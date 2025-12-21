import sqlite3
from pathlib import Path
from core.config import settings

DB_PATH = Path(settings.DATABASE_URL.replace("sqlite:///", ""))

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn