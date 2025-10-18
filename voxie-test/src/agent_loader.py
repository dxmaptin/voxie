"""
spawner/agent_loader.py
Loads agent configuration from Supabase
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json
from supabase import create_client, Client
import os

logger = logging.getLogger("spawner-loader")


@dataclass
class AgentConfigData:
    """Loaded agent configuration from database"""
    id: str
    name: str
    tagline: str
    category: str
    prompt_text: str
    instructions_override: Optional[str]
    voice: str
    model: str
    settings: Dict[str, Any]
    tags: list


class AgentLoader:
    """Loads agent configs from Supabase"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
    
    async def load_agent_config(self, agent_id: str) -> Optional[AgentConfigData]:
        """
        Load agent configuration from Supabase agents table
        
        Uses your existing schema:
        - id: UUID (primary key)
        - name: string (agent name)
        - tagline: string (short description)
        - category: string (business category)
        - prompt_text: text (main instructions)
        - instructions_override: text (optional override)
        - voice: string (openai voice: alloy, echo, fable, onyx, nova, shimmer, marin, coral)
        - model: string (gpt-realtime, etc)
        - settings: JSON object (custom settings)
        - tags: JSON array (tags)
        """
        try:
            logger.info(f"Loading agent config for ID: {agent_id}")
            
            response = self.supabase.table("agents").select("*").eq("id", agent_id).single().execute()
            
            if not response.data:
                logger.warning(f"No agent found with ID: {agent_id}")
                return None
            
            data = response.data
            logger.info(f"Successfully loaded agent: {data.get('name')}")
            
            # Use instructions_override if available, otherwise use prompt_text
            instructions = data.get("instructions_override") or data.get("prompt_text", "")
            
            return AgentConfigData(
                id=data.get("id"),
                name=data.get("name", "Custom Agent"),
                tagline=data.get("tagline", ""),
                category=data.get("category", "general"),
                prompt_text=data.get("prompt_text", ""),
                instructions_override=data.get("instructions_override"),
                voice=data.get("voice", "alloy"),
                model=data.get("model", "gpt-realtime"),
                settings=self._parse_json_field(data.get("settings", {})),
                tags=self._parse_json_field(data.get("tags", []))
            )
        
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return None
    
    def _parse_json_field(self, field: Any) -> Any:
        """Parse JSON field that might be stored as string or already parsed"""
        if isinstance(field, str):
            try:
                return json.loads(field)
            except json.JSONDecodeError:
                return field
        return field if field else ([] if isinstance(field, list) else {})
