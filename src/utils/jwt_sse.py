"""
JWT-based Server-Sent Events (SSE) with heartbeat for enhanced security
"""
import jwt
import time
import asyncio
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from fastapi.responses import StreamingResponse

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("BACKEND_API_KEY", "default_secret_change_me"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60  # 1 hour

class SSEConnectionManager:
    """Manages active SSE connections with JWT authentication"""

    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
        self.heartbeat_interval = 30  # seconds

    def generate_jwt_token(self, job_id: str, user_id: Optional[str] = None) -> str:
        """Generate JWT token for SSE connection"""
        payload = {
            "job_id": job_id,
            "user_id": user_id or "anonymous",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES),
            "type": "sse_token"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token for SSE connection"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "sse_token":
                raise jwt.InvalidTokenError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="SSE token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid SSE token: {str(e)}")

    def register_connection(self, connection_id: str, job_id: str, user_id: str = None):
        """Register a new SSE connection"""
        self.active_connections[connection_id] = {
            "job_id": job_id,
            "user_id": user_id or "anonymous",
            "connected_at": time.time(),
            "last_heartbeat": time.time()
        }

    def unregister_connection(self, connection_id: str):
        """Unregister an SSE connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

    def cleanup_expired_connections(self):
        """Remove inactive connections (cleanup task)"""
        current_time = time.time()
        expired_connections = []

        for connection_id, connection_info in self.active_connections.items():
            # Remove connections inactive for more than 5 minutes
            if current_time - connection_info["last_heartbeat"] > 300:
                expired_connections.append(connection_id)

        for connection_id in expired_connections:
            self.unregister_connection(connection_id)

        return len(expired_connections)

    def update_heartbeat(self, connection_id: str):
        """Update heartbeat for active connection"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id]["last_heartbeat"] = time.time()

# Global connection manager instance
sse_manager = SSEConnectionManager()

def require_sse_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency to validate SSE JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="SSE token required")

    # Extract token from "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    return sse_manager.verify_jwt_token(token)

def create_sse_heartbeat_event(connection_id: str = None) -> str:
    """Create heartbeat event for SSE"""
    heartbeat_data = {
        "type": "heartbeat",
        "timestamp": time.time(),
        "connection_id": connection_id
    }
    return f"data: {json.dumps(heartbeat_data)}\n\n"

def create_sse_connection_event(job_id: str, connection_id: str) -> str:
    """Create connection established event"""
    connection_data = {
        "type": "connection_established",
        "job_id": job_id,
        "connection_id": connection_id,
        "timestamp": time.time(),
        "heartbeat_interval": sse_manager.heartbeat_interval
    }
    return f"data: {json.dumps(connection_data)}\n\n"

async def sse_event_generator_with_heartbeat(job_id: str, connection_id: str, token_payload: Dict[str, Any]):
    """Enhanced SSE event generator with JWT authentication and heartbeat"""

    # Register connection
    sse_manager.register_connection(connection_id, job_id, token_payload.get("user_id"))

    try:
        # Send connection established event
        yield create_sse_connection_event(job_id, connection_id)

        # Initialize tracking
        last_status = None
        heartbeat_counter = 0
        cleanup_counter = 0

        while True:
            current_time = time.time()
            heartbeat_counter += 1
            cleanup_counter += 1

            # Periodic cleanup (every 10 iterations)
            if cleanup_counter >= 10:
                cleanup_counter = 0
                expired_count = sse_manager.cleanup_expired_connections()
                if expired_count > 0:
                    cleanup_event = {
                        "type": "cleanup",
                        "expired_connections": expired_count,
                        "active_connections": len(sse_manager.active_connections)
                    }
                    yield f"data: {json.dumps(cleanup_event)}\n\n"

            # Send heartbeat every heartbeat_interval seconds (assuming 2-second sleep)
            if heartbeat_counter >= (sse_manager.heartbeat_interval // 2):
                heartbeat_counter = 0
                sse_manager.update_heartbeat(connection_id)
                yield create_sse_heartbeat_event(connection_id)

            # Check job status
            from core.db import get_conn
            conn = get_conn()
            cursor = conn.execute("""
                SELECT state, progress FROM jobs WHERE job_id = ?
            """, (job_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                error_data = {
                    'type': 'error',
                    'message': 'Job not found',
                    'job_id': job_id,
                    'connection_id': connection_id,
                    'timestamp': current_time
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break

            current_state, current_progress = row[0], row[1]
            current_status = f"{current_state}:{current_progress}"

            # Only send update if status changed
            if current_status != last_status:
                event_data = {
                    'type': 'job_update',
                    'job_id': job_id,
                    'state': current_state,
                    'progress': current_progress,
                    'timestamp': current_time,
                    'connection_id': connection_id
                }
                yield f"data: {json.dumps(event_data)}\n\n"
                last_status = current_status

            # If job is complete or error, close stream gracefully
            if current_state in ['done', 'error']:
                completion_data = {
                    'type': 'stream_complete',
                    'job_id': job_id,
                    'final_state': current_state,
                    'connection_id': connection_id,
                    'timestamp': current_time
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                break

            # Poll every 2 seconds
            await asyncio.sleep(2)

    except Exception as e:
        # Send error event before disconnecting
        error_data = {
            'type': 'stream_error',
            'error': str(e),
            'job_id': job_id,
            'connection_id': connection_id,
            'timestamp': time.time()
        }
        yield f"data: {json.dumps(error_data)}\n\n"

    finally:
        # Unregister connection
        sse_manager.unregister_connection(connection_id)

# Utility functions for token management
def create_sse_auth_endpoint(job_id: str, user_id: str = None) -> Dict[str, str]:
    """Create SSE authentication response"""
    token = sse_manager.generate_jwt_token(job_id, user_id)
    return {
        "token": token,
        "job_id": job_id,
        "expires_in": JWT_EXPIRATION_MINUTES * 60,  # seconds
        "heartbeat_interval": sse_manager.heartbeat_interval,
        "sse_url": f"/api/jobs/{job_id}/events-stream"
    }