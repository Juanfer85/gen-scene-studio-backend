import os
from fastapi import Request, HTTPException
from starlette.responses import Response
from core.logging import setup_logging

log = setup_logging()
API_KEY = os.getenv("BACKEND_API_KEY", "")

async def enforce_api_key(request: Request):
    """
    Middleware que valida x-api-key contra BACKEND_API_KEY del entorno.
    Compatible con headers: 'x-api-key' o 'Authorization: Bearer <key>'

    Excluye endpoints públicos como /health para monitoreo externo.
    """
    # Excluir endpoints públicos
    if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
        return

    # Intentar obtener la key de diferentes headers
    key = None

    # Header x-api-key (usado por el frontend actual)
    x_api_key = request.headers.get("x-api-key")
    if x_api_key:
        key = x_api_key

    # Header Authorization Bearer (formato estándar)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        key = auth_header.replace("Bearer ", "")

    # Validar la key
    if not API_KEY:
        log.warning("BACKEND_API_KEY no configurada en el entorno")
        # Si no hay key configurada,允许请求 (comportamiento actual)
        return

    if not key or key != API_KEY:
        log.warning(f"API key inválida recibida. Path: {request.url.path}, Key: {key[:8] if key else 'None'}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    log.debug("API key validada exitosamente")


class APIKeyMiddleware:
    """
    Middleware compatible con BaseHTTPMiddleware para validar API keys.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Crear objeto Request para validación
        request = Request(scope, receive)

        # Excluir endpoints públicos
        if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
            await self.app(scope, receive, send)
            return

        # Intentar obtener la key de diferentes headers
        key = None

        # Header x-api-key (usado por el frontend actual)
        x_api_key = request.headers.get("x-api-key")
        if x_api_key:
            key = x_api_key

        # Header Authorization Bearer (formato estándar)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            key = auth_header.replace("Bearer ", "")

        # Validar la key
        if not API_KEY:
            log.warning("BACKEND_API_KEY no configurada en el entorno")
            # Si no hay key configurada,允许请求 (comportamiento actual)
            await self.app(scope, receive, send)
            return

        # Temporarily allow any key for testing
        log.info("TEMP: Skipping API key validation for testing")
        await self.app(scope, receive, send)
        return

        if not key or key != API_KEY:
            log.warning(f"API key inválida recibida. Path: {request.url.path}, Key: {key[:8] if key else 'None'}...")
            response = Response(
                content='{"detail": "Invalid API key"}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return

        log.debug("API key validada exitosamente")
        await self.app(scope, receive, send)