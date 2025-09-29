"""
Production Bridge for LiveKit Agent to WebSocket Communication
Connects your deployed LiveKit agent with the WebSocket server
Enhanced with bidirectional progress callbacks for real-time agent feedback
"""

import os
import requests
import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

logger = logging.getLogger("production-bridge")

class ProductionEventBridge:
    """Bridge that sends events from LiveKit Agent to WebSocket Server with bidirectional callbacks"""

    def __init__(self, webhook_server_url: Optional[str] = None):
        self.webhook_server_url = webhook_server_url or os.environ.get(
            'WEBHOOK_SERVER_URL',
            'https://voxie-production.up.railway.app'  # Updated with actual Railway URL
        )
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout

        # Agent callback system for bidirectional communication
        self.agent_callbacks: Dict[str, Callable] = {}

        logger.info(f"🔗 Production bridge initialized with URL: {self.webhook_server_url}")

    def register_agent_session(self, session_id: str, agent_callback: Callable[[str, str, str], Awaitable[None]]):
        """
        Register a Voxie agent to receive progress updates for a specific session

        Args:
            session_id: Unique session identifier
            agent_callback: Async function(step_name, status, message) to call with updates
        """
        self.agent_callbacks[session_id] = agent_callback
        logger.info(f"🤖 Agent registered for session: {session_id}")

    def unregister_agent_session(self, session_id: str):
        """Remove agent callback registration"""
        if session_id in self.agent_callbacks:
            del self.agent_callbacks[session_id]
            logger.info(f"🤖 Agent unregistered for session: {session_id}")

    async def _notify_agent(self, session_id: str, step_name: str, status: str, message: str):
        """Notify registered agent of progress update"""
        if session_id in self.agent_callbacks:
            try:
                callback = self.agent_callbacks[session_id]
                await callback(step_name, status, message)
                logger.debug(f"🔄 Agent notified: {step_name}:{status}")
            except Exception as e:
                logger.warning(f"⚠️ Agent callback failed: {e}")

    def emit_step(self, session_id: str, step_name: str, status: str,
                  message: str, error: Optional[str] = None, **extra_data):
        """
        Send step update to WebSocket server via HTTP webhook AND notify agent
        """
        try:
            event_data = {
                'session_id': session_id,
                'step': step_name,
                'status': status,
                'message': message,
                'error': error,
                'timestamp': datetime.now().isoformat(),
                **extra_data
            }

            # Send to webhook server (for frontend)
            response = self.session.post(
                f'{self.webhook_server_url}/agent-event',
                json=event_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info(f"✅ Event sent: {step_name}:{status}")
            else:
                logger.warning(f"⚠️ Event send failed: {response.status_code}")

            # Notify agent callback (non-blocking)
            if session_id in self.agent_callbacks:
                asyncio.create_task(self._notify_agent(session_id, step_name, status, message))

        except requests.exceptions.RequestException as e:
            # Fail silently - don't break agent if webhook server is down
            logger.warning(f"⚠️ Webhook server unreachable: {e}")

            # Still try to notify agent even if webhook fails
            if session_id in self.agent_callbacks:
                asyncio.create_task(self._notify_agent(session_id, step_name, status, message))

        except Exception as e:
            logger.error(f"❌ Bridge error: {e}")

    def emit_overall_status(self, session_id: str, status: str, message: str,
                          error: Optional[str] = None, **extra_data):
        """Emit overall agent creation status"""
        self.emit_step(session_id, 'overall', status, message, error, **extra_data)

        # Clean up session when completed or failed
        if status in ['completed', 'failed']:
            self.unregister_agent_session(session_id)

    def emit_action(self, session_id: str, action_type: str, status: str,
                   message: str, tool_data: Optional[Dict] = None, error: Optional[str] = None):
        """
        Send action-based event for specific frontend tools
        """
        try:
            event_data = {
                'session_id': session_id,
                'action_type': action_type,
                'status': status,
                'message': message,
                'tool_data': tool_data or {},
                'error': error,
                'timestamp': datetime.now().isoformat()
            }

            response = self.session.post(
                f'{self.webhook_server_url}/action-event',
                json=event_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info(f"✅ Action sent: {action_type}:{status}")

        except Exception as e:
            logger.warning(f"⚠️ Action event failed: {e}")

    def test_connection(self) -> bool:
        """Test if webhook server is reachable"""
        try:
            response = self.session.get(f'{self.webhook_server_url}/health', timeout=3)
            return response.status_code == 200
        except:
            return False

    def get_active_sessions(self) -> list:
        """Get list of active session IDs with registered agents"""
        return list(self.agent_callbacks.keys())

# Global bridge instance for production
production_bridge = None

def initialize_production_bridge(webhook_server_url: Optional[str] = None):
    """Initialize the production bridge"""
    global production_bridge
    production_bridge = ProductionEventBridge(webhook_server_url)

    if production_bridge.test_connection():
        logger.info(f"✅ Production bridge connected to {production_bridge.webhook_server_url}")
    else:
        logger.warning(f"⚠️ Production bridge cannot reach {production_bridge.webhook_server_url}")

    return production_bridge