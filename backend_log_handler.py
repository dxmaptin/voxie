"""
Custom Logging Handler that sends logs to backend automatically
This way you don't need to manually add event_logger calls everywhere
"""

import logging
import asyncio
import aiohttp
from typing import Optional

class BackendLogHandler(logging.Handler):
    """
    Logging handler that sends log messages to backend API
    Use this to automatically stream ALL logs to your backend
    """

    def __init__(self, session_id: str, backend_url: str = "http://localhost:8000"):
        super().__init__()
        self.session_id = session_id
        self.backend_url = backend_url
        self.loop = None

    def emit(self, record: logging.LogRecord):
        """Send log record to backend"""
        try:
            # Format the log message
            message = self.format(record)

            # Determine status from log level
            status_map = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'error'
            }
            status = status_map.get(record.levelname, 'info')

            # Send to backend asynchronously
            if self.loop is None:
                try:
                    self.loop = asyncio.get_event_loop()
                except RuntimeError:
                    return  # No event loop available

            self.loop.create_task(self._send_log(status, message, record))

        except Exception:
            self.handleError(record)

    async def _send_log(self, status: str, message: str, record: logging.LogRecord):
        """Actually send the log to backend"""
        try:
            event = {
                "status": status,
                "message": message,
                "timestamp": record.created,
                "level": record.levelname,
                "logger": record.name
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/agents/{self.session_id}/log",
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    pass  # Ignore response

        except Exception:
            pass  # Don't fail if backend is down


# How to use in your agent.py:

"""
# At the top of your entrypoint function:

async def entrypoint(ctx: agents.JobContext):
    # Get session ID
    session_id = f"{ctx.room.name}_{uuid.uuid4().hex[:8]}"

    # Add backend logging handler (if backend is available)
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    if os.getenv("ENABLE_BACKEND_LOGGING", "false").lower() == "true":
        # Create handler
        backend_handler = BackendLogHandler(
            session_id=session_id,
            backend_url=backend_url
        )

        # Set format
        backend_handler.setFormatter(
            logging.Formatter('%(message)s')  # Just the message, emojis included
        )

        # Add to your loggers
        logging.getLogger("multi-agent").addHandler(backend_handler)
        logging.getLogger("call-analytics").addHandler(backend_handler)
        logging.getLogger("transcription").addHandler(backend_handler)

        print(f"✅ Backend logging enabled for session: {session_id}")

    # Rest of your code...
"""
