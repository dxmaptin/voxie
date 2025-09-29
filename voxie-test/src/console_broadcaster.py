"""
Console Event Broadcaster for Terminal Logging
Shows real-time agent creation events in the terminal when running Voxie
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("console-broadcaster")

class ConsoleEventBroadcaster:
    """Event broadcaster that logs to console/terminal"""

    def __init__(self):
        self.session_events = {}

    def emit_step(self, session_id: str, step_name: str, status: str,
                  message: str, error: Optional[str] = None, **extra_data):
        """
        Emit a step update to the console
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Format the log message
            log_msg = f"📡 [{timestamp}] {step_name}:{status} - {message}"

            if extra_data.get('agent_name'):
                log_msg += f" | Agent: {extra_data['agent_name']}"
            if extra_data.get('voice_model'):
                log_msg += f" | Voice: {extra_data['voice_model']}"
            if error:
                log_msg += f" | Error: {error}"

            # Print to console
            print(log_msg)

            # Also log via Python logging
            logger.info(f"{step_name}:{status} - {message}")

            # Track events for this session
            if session_id not in self.session_events:
                self.session_events[session_id] = []

            self.session_events[session_id].append({
                'timestamp': timestamp,
                'step': step_name,
                'status': status,
                'message': message,
                'error': error,
                **extra_data
            })

        except Exception as e:
            print(f"❌ Failed to emit console event: {e}")
            logger.error(f"Console event emission failed: {e}")

    def emit_overall_status(self, session_id: str, status: str, message: str,
                          error: Optional[str] = None, **extra_data):
        """Emit overall agent creation status"""
        self.emit_step(session_id, 'overall', status, message, error, **extra_data)

        # Print summary for completed/failed
        if status in ['completed', 'failed']:
            print("=" * 60)
            if status == 'completed':
                print("🎉 Agent Creation Completed Successfully!")
                if extra_data.get('agent_name'):
                    print(f"✅ Agent Name: {extra_data['agent_name']}")
            else:
                print("❌ Agent Creation Failed!")
                if error:
                    print(f"❌ Error: {error}")
            print("=" * 60)

    def get_session_events(self, session_id: str):
        """Get all events for a session"""
        return self.session_events.get(session_id, [])

# Create global console broadcaster
console_broadcaster = ConsoleEventBroadcaster()