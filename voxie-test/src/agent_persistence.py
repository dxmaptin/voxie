"""
Agent Persistence - Records agent configurations for reproducibility
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from supabase_client import supabase_client


class AgentPersistence:
    """Save and load agent configurations"""

    @staticmethod
    def save_agent_config(
        user_requirements: Dict[str, Any],
        processed_spec: Dict[str, Any],
        session_id: Optional[str] = None,
        room_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Save complete agent configuration

        Returns:
            agent_id if successful
        """
        try:
            business_name = user_requirements.get('business_name', 'Unknown')
            business_type = user_requirements.get('business_type', 'general')

            agent_data = {
                'id': str(uuid.uuid4()),
                'name': processed_spec.get('agent_type', f"{business_name} Agent"),
                'avatar_url': f"https://picsum.photos/seed/{business_name.lower().replace(' ', '-')}/200",
                'tagline': f"AI assistant for {business_name}",
                'category': business_type.title(),
                'language': ['EN'],
                'prompt_source': 'text',
                'prompt_text': processed_spec.get('instructions', ''),
                'prompt_variables': user_requirements,
                'voice': processed_spec.get('voice', 'alloy'),
                'model': 'gpt-realtime',
                'provider': 'openai_realtime',
                'provider_config': {
                    'voice': processed_spec.get('voice', 'alloy'),
                    'business_type': business_type
                },
                'settings': {
                    'business_context': processed_spec.get('business_context', {}),
                    'functions': processed_spec.get('functions', []),
                    'sample_responses': processed_spec.get('sample_responses', []),
                    'session_id': session_id,
                    'room_id': room_id,
                    'created_via': 'voxie_transfer'
                },
                'status': 'draft',
                'status_type': 'testing',
                'visibility': 'listed',
                'access_mode': 'open',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            response = supabase_client.client.table('agents').insert(agent_data).execute()

            if response.data:
                agent_id = response.data[0]['id']
                print(f"✅ Agent saved: {agent_id}")
                print(f"   Business: {business_name}")
                print(f"   Type: {business_type}")
                print(f"   Voice: {processed_spec.get('voice')}")
                return agent_id

            return None

        except Exception as e:
            print(f"❌ Error saving agent: {e}")
            return None

    @staticmethod
    def load_agent_config(agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent configuration by ID"""
        try:
            response = supabase_client.client.table('agents').select('*').eq('id', agent_id).execute()

            if response.data and len(response.data) > 0:
                agent = response.data[0]
                print(f"✅ Loaded agent: {agent.get('name')}")

                return {
                    'agent_id': agent.get('id'),
                    'user_requirements': agent.get('prompt_variables', {}),
                    'processed_spec': {
                        'agent_type': agent.get('name'),
                        'instructions': agent.get('prompt_text'),
                        'voice': agent.get('voice'),
                        'functions': agent.get('settings', {}).get('functions', []),
                        'sample_responses': agent.get('settings', {}).get('sample_responses', []),
                        'business_context': agent.get('settings', {}).get('business_context', {})
                    },
                    'metadata': {
                        'session_id': agent.get('settings', {}).get('session_id'),
                        'room_id': agent.get('settings', {}).get('room_id'),
                        'created_at': agent.get('created_at')
                    }
                }

            return None

        except Exception as e:
            print(f"❌ Error loading agent: {e}")
            return None

    @staticmethod
    def list_agents(business_name: Optional[str] = None, limit: int = 20) -> list:
        """List saved agents"""
        try:
            query = supabase_client.client.table('agents').select('id, name, tagline, category, voice, created_at')

            if business_name:
                query = query.ilike('name', f'%{business_name}%')

            response = query.order('created_at', desc=True).limit(limit).execute()

            if response.data:
                print(f"✅ Found {len(response.data)} agents")
                return response.data

            return []

        except Exception as e:
            print(f"❌ Error listing agents: {e}")
            return []
