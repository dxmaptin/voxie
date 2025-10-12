"""
Event Logger - Publishes agent creation events to backend SSE stream
"""

import os
import logging
from typing import Optional
from datetime import datetime
import aiohttp

logger = logging.getLogger("event-logger")

class EventLogger:
    """
    Publishes agent creation events to the backend API
    These events are streamed to the frontend via SSE
    """

    def __init__(self, session_id: Optional[str] = None, backend_url: Optional[str] = None):
        self.session_id = session_id
        self.backend_url = backend_url or os.getenv("BACKEND_URL", "http://localhost:8000")
        self.enabled = session_id is not None

    async def log(self, status: str, message: str, **extra_data):
        """
        Log an event to the backend

        Args:
            status: Event status (starting, processing, completed, error)
            message: Human-readable message (with emoji prefixes like your logs)
            **extra_data: Additional data to include in the event
        """
        if not self.enabled:
            # If no session_id, just log locally
            logger.info(f"[{status}] {message}")
            return

        event = {
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **extra_data
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/agents/{self.session_id}/log",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"Failed to publish event: {resp.status}")
        except Exception as e:
            logger.debug(f"Could not publish event to backend: {e}")
            # Don't fail the main process if backend logging fails
