from __future__ import annotations
import os, hmac, hashlib, json
from typing import Dict, Any
import httpx

NOTIFY_URL = os.getenv("NOTIFY_URL", "").strip()
NOTIFY_SECRET = os.getenv("NOTIFY_SECRET", "").encode("utf-8")
ALLOWED = {e.strip() for e in os.getenv("NOTIFY_EVENTS", "render_done,compose_done").split(",") if e.strip()}

def _signature(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hmac.new(NOTIFY_SECRET or b"", body, hashlib.sha256).hexdigest()

async def send_notify(event: str, payload: Dict[str, Any]) -> bool:
    if not NOTIFY_URL or event not in ALLOWED:
        return False
    headers = {
        "Content-Type": "application/json",
        "X-Event": event,
        "X-Signature-SHA256": _signature(payload),
    }
    timeout = httpx.Timeout(15.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for _ in range(3):
            try:
                r = await client.post(NOTIFY_URL, headers=headers, json=payload)
                if r.status_code < 500:
                    return True
            except Exception:
                pass
    return False