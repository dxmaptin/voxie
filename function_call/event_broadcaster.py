"""
Real-time Event Broadcasting System for Agent Creation
Simple WebSocket-based communication for frontend progress updates
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("event-broadcaster")

class AgentCreationEventBroadcaster:
    """Simple event broadcaster for agent creation progress"""

    def __init__(self, socketio):
        self.socketio = socketio
        self.active_sessions = {}

    def emit_step(self, session_id: str, step_name: str, status: str,
                  message: str, error: Optional[str] = None, **extra_data):
        """
        Emit a step update to the frontend

        Args:
            session_id: Unique session identifier
            step_name: Name of the step (scenario, prompts, voice, etc.)
            status: started, completed, failed
            message: Human readable message
            error: Error details if status is failed
            **extra_data: Additional data like agent_name, voice_model
        """
        try:
            event_data = {
                'step': step_name,
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'error': error,
                **extra_data
            }

            logger.info(f"📡 Broadcasting to {session_id}: {step_name} - {status} - {message}")

            # Emit to specific session room
            self.socketio.emit('agent_creation_update', event_data, room=session_id)

            # Update session tracking
            if session_id in self.active_sessions:
                if 'steps' not in self.active_sessions[session_id]:
                    self.active_sessions[session_id]['steps'] = []
                self.active_sessions[session_id]['steps'].append(event_data)

        except Exception as e:
            logger.error(f"❌ Failed to emit event: {e}")

    def connect_session(self, session_id: str, client_id: str):
        """Register a new session"""
        self.active_sessions[session_id] = {
            'client_id': client_id,
            'connected_at': datetime.now().isoformat(),
            'steps': []
        }
        logger.info(f"🔌 Session connected: {session_id}")

    def disconnect_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"🔌 Session disconnected: {session_id}")

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a session"""
        return self.active_sessions.get(session_id, {})

    def emit_overall_status(self, session_id: str, status: str, message: str, error: Optional[str] = None, **extra_data):
        """Emit overall agent creation status"""
        self.emit_step(session_id, 'overall', status, message, error, **extra_data)

# Global broadcaster instance (will be initialized with socketio)
event_broadcaster = None

def initialize_broadcaster(socketio):
    """Initialize the global event broadcaster"""
    global event_broadcaster
    event_broadcaster = AgentCreationEventBroadcaster(socketio)
    return event_broadcaster