"""
Agent Loader - Loads agent configurations from Supabase database
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'function_call'))

from dotenv import load_dotenv
load_dotenv('.env.local')

logger = logging.getLogger("agent-loader")


class AgentLoader:
    """Loads agent configurations from Supabase"""

    @staticmethod
    async def load_agent(agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a complete agent configuration from Supabase

        Args:
            agent_id: The UUID of the agent to load

        Returns:
            Dict containing all agent configuration, or None if not found
        """
        try:
            from supabase_client import supabase_client

            logger.info(f"📥 Loading agent from database: {agent_id}")

            # Fetch agent from Supabase
            response = supabase_client.client.table('agents')\
                .select('*')\
                .eq('id', agent_id)\
                .execute()

            if not response.data or len(response.data) == 0:
                logger.error(f"❌ Agent not found: {agent_id}")
                return None

            agent_data = response.data[0]
            logger.info(f"✅ Loaded agent: {agent_data.get('name')}")
            logger.info(f"   Type: {agent_data.get('category')}")
            logger.info(f"   Voice: {agent_data.get('voice')}")
            logger.info(f"   Status: {agent_data.get('status')}")

            # Transform database format to spawner format
            spawner_config = AgentLoader._transform_to_spawner_format(agent_data)

            return spawner_config

        except Exception as e:
            logger.error(f"❌ Failed to load agent {agent_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    @staticmethod
    def _transform_to_spawner_format(agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform database format to spawner-friendly format

        Database has:
        - prompt_text: The instructions
        - prompt_variables: User requirements
        - settings: Business context, functions, etc.
        - provider_config: Voice and model settings

        Spawner needs:
        - instructions: Clear prompt text
        - voice: Voice to use
        - functions: List of available functions
        - business_context: Business-specific data
        - greeting: Optional custom greeting
        """

        settings = agent_data.get('settings', {})
        prompt_variables = agent_data.get('prompt_variables', {})
        provider_config = agent_data.get('provider_config', {})

        # Extract business context
        business_context = settings.get('business_context', {})
        if not business_context:
            # Fallback: construct from prompt_variables
            business_context = {
                'business_name': prompt_variables.get('business_name'),
                'business_type': prompt_variables.get('business_type'),
                'tone': prompt_variables.get('tone'),
                'functions': prompt_variables.get('main_functions', [])
            }

        # Extract greeting if available
        greeting = None
        special_reqs = prompt_variables.get('special_requirements', [])
        for req in special_reqs:
            if 'greeting' in req.lower():
                # Extract greeting text
                parts = req.split(':', 1)
                if len(parts) > 1:
                    greeting = parts[1].strip()
                    break

        # Get agent name from special requirements or business context
        agent_name = None
        for req in special_reqs:
            if 'agent name' in req.lower():
                parts = req.split(':', 1)
                if len(parts) > 1:
                    agent_name = parts[1].strip()
                    break

        if not agent_name:
            agent_name = business_context.get('agent_name')

        return {
            'id': agent_data.get('id'),
            'name': agent_data.get('name'),
            'agent_name': agent_name,  # The character name (e.g., "Charlie")
            'category': agent_data.get('category'),
            'voice': agent_data.get('voice', 'alloy'),
            'model': agent_data.get('model', 'gpt-realtime'),
            'instructions': agent_data.get('prompt_text', ''),
            'functions': settings.get('functions', []),
            'sample_responses': settings.get('sample_responses', []),
            'business_context': business_context,
            'greeting': greeting,
            'prompt_variables': prompt_variables,
            'settings': settings,
            'status': agent_data.get('status'),
            'created_at': agent_data.get('created_at'),
            'updated_at': agent_data.get('updated_at')
        }

    @staticmethod
    async def list_active_agents(limit: int = 50) -> list:
        """
        List all active/spawnable agents

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of agent summaries
        """
        try:
            from supabase_client import supabase_client

            response = supabase_client.client.table('agents')\
                .select('id, name, category, voice, status, created_at')\
                .in_('status', ['active', 'draft'])\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()

            if response.data:
                logger.info(f"📋 Found {len(response.data)} spawnable agents")
                return response.data

            return []

        except Exception as e:
            logger.error(f"❌ Failed to list agents: {e}")
            return []
