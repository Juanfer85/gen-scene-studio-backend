import sqlite3
from contextlib import contextmanager
from typing import Generator
import logging

from .db import get_conn


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para manejar conexiones a la base de datos de forma segura.

    Asegura que las conexiones siempre se cierren, incluso si ocurren excepciones.

    Usage:
        with get_db_connection() as conn:
            # Usar la conexión conn
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs")
            results = cursor.fetchall()
        # La conexión se cierra automáticamente al salir del bloque
    """
    conn = None
    try:
        conn = get_conn()
        yield conn
    except Exception as e:
        # Loggear el error para debugging
        logger = logging.getLogger(__name__)
        logger.exception(f"Database operation failed: {e}")
        # Re-lanzar la excepción para que el código superior la maneje
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                # Loggear error al cerrar conexión, pero no lanzar excepción
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to close database connection: {e}")


@contextmanager
def get_db_connection_with_error_handler(job_id: str = None, operation: str = "database operation") -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager con manejo específico de errores para operaciones de jobs.

    Similar a get_db_connection() pero con contexto específico para mejor logging.

    Args:
        job_id: ID del job para contexto en logs
        operation: Descripción de la operación para contexto en logs
    """
    conn = None
    try:
        conn = get_conn()
        yield conn
    except Exception as e:
        # Loggear con contexto específico
        logger = logging.getLogger(__name__)
        job_context = f"job_id={job_id}" if job_id else "unknown job"
        logger.exception(f"Database operation '{operation}' failed for {job_context}: {e}")
        # Re-lanzar la excepción
        raise
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to close database connection after {operation}: {e}")