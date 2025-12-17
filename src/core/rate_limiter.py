"""
Rate Limiter Distribuido con SQLite
Implementación robusta que funciona en entornos multi-proceso
"""
import time
import sqlite3
import threading
from pathlib import Path
from typing import Optional, Tuple
from contextlib import contextmanager
import logging
from fastapi import HTTPException, Request

log = logging.getLogger(__name__)

class DistributedRateLimiter:
    """
    Rate limiter distribuido usando SQLite con atomicidad garantizada.
    Soporta múltiples procesos y containers concurrentemente.
    """

    def __init__(self, db_path: str, cleanup_interval: int = 300):
        """
        Inicializa el rate limiter distribuido.

        Args:
            db_path: Path al archivo SQLite para rate limiting
            cleanup_interval: Segundos entre limpiezas automáticas
        """
        self.db_path = Path(db_path)
        self.cleanup_interval = cleanup_interval
        self._local_cache = {}  # Caché local para reducir DB hits
        self._last_cleanup = 0
        self._lock = threading.Lock()

        # Inicializar base de datos
        self._init_db()

        # Limpieza automática en thread separado
        self._start_cleanup_thread()

    def _init_db(self):
        """Inicializa la base de datos SQLite con la estructura necesaria."""
        try:
            # Asegurar que el directorio exista
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Conexión con timeout y modo serializado para atomicidad
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                isolation_level='EXCLUSIVE'
            )

            # Configuraciones de SQLite para concurrencia
            conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
            conn.execute('PRAGMA synchronous=NORMAL')  # Balance seguridad/rendimiento
            conn.execute('PRAGMA busy_timeout=30000')  # 30s timeout

            # Tabla de rate limiting
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    client_key TEXT NOT NULL,
                    request_time REAL NOT NULL,
                    created_at INTEGER NOT NULL,
                    PRIMARY KEY (client_key, request_time)
                )
            ''')

            # Índices para performance
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_rate_limits_client_time
                ON rate_limits(client_key, request_time)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_rate_limits_created_at
                ON rate_limits(created_at)
            ''')

            conn.commit()
            conn.close()

            log.info(f"Rate limiter initialized: {self.db_path}")

        except Exception as e:
            log.error(f"Failed to initialize rate limiter DB: {e}")
            raise

    def _start_cleanup_thread(self):
        """Inicia un thread para limpieza automática periódica."""
        import threading

        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_records()
                    time.sleep(self.cleanup_interval)
                except Exception as e:
                    log.error(f"Rate limiter cleanup error: {e}")
                    time.sleep(60)  # Esperar 1min si hay error

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        log.info("Rate limiter cleanup thread started")

    @contextmanager
    def _get_connection(self):
        """Context manager para conexión a DB con configuraciones optimizadas."""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                isolation_level='IMMEDIATE'  # Lock inmediato para escrituras
            )

            # Configuraciones de SQLite
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA busy_timeout=30000')

            yield conn

        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _cleanup_old_records(self):
        """Limpia registros antiguos (más de 2 minutos)."""
        cutoff_time = time.time() - 120  # 2 minutos para safety margin

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'DELETE FROM rate_limits WHERE created_at < ?',
                    (int(cutoff_time),)
                )
                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    log.info(f"Rate limiter cleanup: removed {deleted_count} old records")

                # Vacuum periódico para optimizar DB
                if time.time() - self._last_cleanup > 3600:  # Cada hora
                    conn.execute('VACUUM')
                    self._last_cleanup = time.time()

        except Exception as e:
            log.error(f"Rate limiter cleanup failed: {e}")

    def _get_client_key(self, request: Request) -> str:
        """
        Genera una clave única para el cliente basada en IP y otros headers.
        Más robusto que solo IP para prevenir bypassing.
        """
        # IP principal
        client_ip = request.client.host if request.client else "unknown"

        # Headers adicionales para identificación más robusta
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        real_ip = request.headers.get("X-Real-IP", "")
        user_agent = request.headers.get("User-Agent", "")[:50]  # Primeros 50 chars

        # Combinar para crear clave única
        key_parts = [client_ip]

        if forwarded_for:
            key_parts.append(f"xff:{forwarded_for.split(',')[0].strip()}")
        if real_ip:
            key_parts.append(f"rip:{real_ip}")
        if user_agent:
            key_parts.append(f"ua:{hash(user_agent)}")

        return "|".join(key_parts)

    def check_rate_limit(self, request: Request, limit: int = 120, window_seconds: int = 60) -> bool:
        """
        Verifica si la solicitud debe ser permitida según rate limit.

        Args:
            request: Objeto Request de FastAPI
            limit: Límite de solicitudes (default: 120 por minuto)
            window_seconds: Ventana de tiempo en segundos (default: 60)

        Returns:
            True si la solicitud es permitida, False si excede el límite
        """
        client_key = self._get_client_key(request)
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        try:
            with self._get_connection() as conn:
                # Contar solicitudes recientes en ventana
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM rate_limits
                    WHERE client_key = ? AND request_time > ?
                ''', (client_key, cutoff_time))

                recent_count = cursor.fetchone()[0]

                # Si no excede límite, registrar nueva solicitud
                if recent_count < limit:
                    conn.execute('''
                        INSERT INTO rate_limits (client_key, request_time, created_at)
                        VALUES (?, ?, ?)
                    ''', (client_key, current_time, int(current_time)))

                    conn.commit()
                    log.debug(f"Rate limit check passed: {client_key} ({recent_count + 1}/{limit})")
                    return True
                else:
                    log.warning(f"Rate limit exceeded: {client_key} ({recent_count}/{limit})")
                    return False

        except Exception as e:
            log.error(f"Rate limit check failed for {client_key}: {e}")
            # En caso de error, fallback a allow (fail-open)
            return True

    def get_client_stats(self, request: Request) -> dict:
        """
        Obtiene estadísticas de rate limiting para un cliente.
        Útil para debugging y monitoring.
        """
        client_key = self._get_client_key(request)
        current_time = time.time()

        try:
            with self._get_connection() as conn:
                # Solicitudes en última hora
                hour_ago = current_time - 3600
                cursor = conn.execute(
                    'SELECT COUNT(*) FROM rate_limits WHERE client_key = ? AND request_time > ?',
                    (client_key, hour_ago)
                )
                last_hour_count = cursor.fetchone()[0]

                # Solicitudes en último minuto
                minute_ago = current_time - 60
                cursor = conn.execute(
                    'SELECT COUNT(*) FROM rate_limits WHERE client_key = ? AND request_time > ?',
                    (client_key, minute_ago)
                )
                last_minute_count = cursor.fetchone()[0]

                # Última solicitud
                cursor = conn.execute(
                    'SELECT MAX(request_time) FROM rate_limits WHERE client_key = ?',
                    (client_key,)
                )
                last_request = cursor.fetchone()[0]

                return {
                    "client_key": client_key,
                    "last_minute_requests": last_minute_count,
                    "last_hour_requests": last_hour_count,
                    "last_request_time": last_request,
                    "seconds_since_last_request": current_time - last_request if last_request else None
                }

        except Exception as e:
            log.error(f"Failed to get rate limit stats for {client_key}: {e}")
            return {
                "client_key": client_key,
                "error": str(e)
            }

# Instancia global del rate limiter
_rate_limiter: Optional[DistributedRateLimiter] = None

def init_rate_limiter(db_path: str, cleanup_interval: int = 300) -> None:
    """Inicializa el rate limiter global."""
    global _rate_limiter
    _rate_limiter = DistributedRateLimiter(db_path, cleanup_interval)

def get_rate_limiter() -> DistributedRateLimiter:
    """Obtiene la instancia del rate limiter global."""
    if _rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized. Call init_rate_limiter() first.")
    return _rate_limiter

def check_rate_limit(request: Request, limit: Optional[int] = None, window_seconds: Optional[int] = None) -> bool:
    """
    Función de conveniencia para verificar rate limit.
    Usa la configuración de settings si no se especifican límites.
    """
    from .config import settings

    if limit is None:
        limit = int(settings.RATE_LIMIT_RPM or 120)
    if window_seconds is None:
        window_seconds = 60

    return get_rate_limiter().check_rate_limit(request, limit, window_seconds)

def rate_limit_dependency(request: Request):
    """
    Dependencia de FastAPI para rate limiting.
    Lanza HTTPException 429 si se excede el límite.
    """
    if not check_rate_limit(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )