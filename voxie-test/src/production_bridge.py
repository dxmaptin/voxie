"""
Production Bridge for LiveKit Agent to WebSocket Communication
Connects your deployed LiveKit agent with the WebSocket server
"""

import os
import requests
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("production-bridge")

class ProductionEventBridge:
    """Bridge that sends events from LiveKit Agent to WebSocket Server"""

    def __init__(self, webhook_server_url: Optional[str] = None):
        self.webhook_server_url = webhook_server_url or os.environ.get(
            'WEBHOOK_SERVER_URL',
            'https://your-app.railway.app'  # Will be replaced with actual Railway URL
        )
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout

    def emit_step(self, session_id: str, step_name: str, status: str,
                  message: str, error: Optional[str] = None, **extra_data):
        """
        Send step update to WebSocket server via HTTP webhook
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

            # Send to webhook server
            response = self.session.post(
                f'{self.webhook_server_url}/agent-event',
                json=event_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info(f"✅ Event sent: {step_name}:{status}")
            else:
                logger.warning(f"⚠️ Event send failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            # Fail silently - don't break agent if webhook server is down
            logger.warning(f"⚠️ Webhook server unreachable: {e}")
        except Exception as e:
            logger.error(f"❌ Bridge error: {e}")

    def emit_overall_status(self, session_id: str, status: str, message: str,
                          error: Optional[str] = None, **extra_data):
        """Emit overall agent creation status"""
        self.emit_step(session_id, 'overall', status, message, error, **extra_data)

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