"""
Integration layer between WebSocket server and Agent Creation System
Bridges the HTTP/WebSocket webhook server with the LiveKit agent system
"""

import sys
import os
import asyncio
import logging
from typing import Optional

# Add paths to import agent modules
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_dir = os.path.join(os.path.dirname(current_dir), 'voxie-test', 'src')
sys.path.append(agent_dir)

try:
    from agent import AgentManager, UserRequirements
    print("✅ Successfully imported agent modules")
except ImportError as e:
    print(f"❌ Failed to import agent modules: {e}")
    AgentManager = None
    UserRequirements = None

logger = logging.getLogger("agent-integration")

class AgentCreationIntegrator:
    """
    Integrates WebSocket-based agent creation requests with the actual agent system
    """

    def __init__(self, event_broadcaster):
        self.event_broadcaster = event_broadcaster
        self.agent_manager = None
        self.active_creations = {}  # Track active creation sessions

        # Initialize agent manager if available
        if AgentManager:
            self.agent_manager = AgentManager(event_broadcaster=event_broadcaster)
            logger.info("✅ Agent manager initialized")
        else:
            logger.error("❌ Agent manager not available")

    async def start_agent_creation(self, session_id: str, requirements_data: dict):
        """
        Start real agent creation process using the actual agent system

        Args:
            session_id: WebSocket session ID
            requirements_data: Frontend requirements data
        """
        try:
            if not self.agent_manager or not UserRequirements:
                logger.error("❌ Agent system not available")
                self.event_broadcaster.emit_overall_status(
                    session_id,
                    'failed',
                    'Agent creation system not available',
                    error='Agent modules not properly imported'
                )
                return

            logger.info(f"🚀 Starting real agent creation for session: {session_id}")

            # Convert frontend requirements to UserRequirements
            user_requirements = self._convert_requirements(requirements_data)

            # Set up agent manager for this session
            self.agent_manager.set_session_id(session_id)
            self.agent_manager.user_requirements = user_requirements

            # Track this creation session
            self.active_creations[session_id] = {
                'requirements': user_requirements,
                'status': 'in_progress',
                'started_at': asyncio.get_event_loop().time()
            }

            # Emit initial status
            self.event_broadcaster.emit_overall_status(
                session_id,
                'started',
                'Initializing agent creation process...'
            )

            # Start the actual agent creation process
            await self.agent_manager.transition_to_processing(session_id)

            # Update session status
            if session_id in self.active_creations:
                self.active_creations[session_id]['status'] = 'completed'

        except Exception as e:
            logger.error(f"❌ Agent creation failed for session {session_id}: {e}")

            # Update session status
            if session_id in self.active_creations:
                self.active_creations[session_id]['status'] = 'failed'
                self.active_creations[session_id]['error'] = str(e)

            # Emit error
            self.event_broadcaster.emit_overall_status(
                session_id,
                'failed',
                'Agent creation failed',
                error=str(e)
            )

    def _convert_requirements(self, requirements_data: dict) -> 'UserRequirements':
        """Convert frontend requirements data to UserRequirements object"""
        if not UserRequirements:
            raise Exception("UserRequirements class not available")

        requirements = UserRequirements()

        # Map frontend data to UserRequirements fields
        requirements.business_name = requirements_data.get('business_name', '')
        requirements.business_type = requirements_data.get('business_type', '')
        requirements.target_audience = requirements_data.get('target_audience', '')
        requirements.tone = requirements_data.get('tone', '')

        # Handle functions as list
        if 'main_functions' in requirements_data:
            if isinstance(requirements_data['main_functions'], list):
                requirements.main_functions = requirements_data['main_functions']
            else:
                requirements.main_functions = [requirements_data['main_functions']]

        # Handle special requirements
        if 'special_requirements' in requirements_data:
            if isinstance(requirements_data['special_requirements'], list):
                requirements.special_requirements = requirements_data['special_requirements']
            else:
                requirements.special_requirements = [requirements_data['special_requirements']]

        # Handle contact info
        if 'contact_info' in requirements_data:
            requirements.contact_info = requirements_data['contact_info']

        logger.info(f"📋 Converted requirements: {requirements.business_name} - {requirements.business_type}")
        return requirements

    def get_session_status(self, session_id: str) -> dict:
        """Get current status of an agent creation session"""
        return self.active_creations.get(session_id, {})

    def cleanup_session(self, session_id: str):
        """Clean up completed or failed session"""
        if session_id in self.active_creations:
            del self.active_creations[session_id]
            logger.info(f"🧹 Cleaned up session: {session_id}")

# Global integrator instance
agent_integrator = None

def initialize_agent_integrator(event_broadcaster):
    """Initialize the global agent integrator"""
    global agent_integrator
    agent_integrator = AgentCreationIntegrator(event_broadcaster)
    return agent_integrator