"""
spawner.py - Single File Dynamic Agent Spawner
Deploy once, spawn infinite agent configurations from Supabase

Usage:
    python spawner.py start

Environment Variables Required:
    SUPABASE_URL
    SUPABASE_SERVICE_KEY
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET
    OPENAI_API_KEY
"""

import logging
import re
import os
import json
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from livekit import agents
from livekit.agents import JobContext, WorkerOptions
from livekit.plugins import openai, silero
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("spawner")


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AgentConfigData:
    """Agent configuration loaded from Supabase database"""
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
    
    def __post_init__(self):
        """Validate voice after initialization"""
        valid_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
        if self.voice not in valid_voices:
            logger.warning(f"Invalid voice '{self.voice}', defaulting to 'alloy'")
            self.voice = "alloy"


# ============================================================================
# AGENT LOADER - Loads configs from Supabase
# ============================================================================

class AgentLoader:
    """Loads agent configurations from Supabase with optional caching"""
    
    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        """
        Args:
            use_cache: Enable in-memory caching
            cache_ttl: Cache time-to-live in seconds (default 5 minutes)
        """
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment. "
                "Please set these in your .env.local file."
            )
        
        self.supabase: Client = create_client(url, key)
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[AgentConfigData, datetime]] = {}
        
        logger.info("✅ AgentLoader initialized with Supabase connection")
    
    async def load_agent_config(self, agent_id: str) -> Optional[AgentConfigData]:
        """
        Load agent configuration from Supabase agents table
        Uses cache if enabled and not expired
        
        Database Schema Expected:
            - id: UUID (primary key)
            - name: TEXT (agent name)
            - tagline: TEXT (short description)
            - category: TEXT (business category)
            - prompt_text: TEXT (main instructions)
            - instructions_override: TEXT (optional override)
            - voice: TEXT (openai voice)
            - model: TEXT (model name)
            - settings: JSONB (custom settings)
            - tags: JSONB (tags array)
        """
        # Check cache first
        if self.use_cache and agent_id in self._cache:
            config, cached_at = self._cache[agent_id]
            if datetime.now() - cached_at < timedelta(seconds=self.cache_ttl):
                logger.info(f"📦 Using cached config for: {config.name}")
                return config
        
        try:
            logger.info(f"🔄 Loading agent config from database: {agent_id}")
            
            response = self.supabase.table("agents")\
                .select("*")\
                .eq("id", agent_id)\
                .single()\
                .execute()
            
            if not response.data:
                logger.warning(f"⚠️ No agent found with ID: {agent_id}")
                return None
            
            data = response.data
            
            config = AgentConfigData(
                id=data.get("id"),
                name=data.get("name", "Custom Agent"),
                tagline=data.get("tagline", ""),
                category=data.get("category", "general"),
                prompt_text=data.get("prompt_text", ""),
                instructions_override=data.get("instructions_override"),
                voice=data.get("voice", "alloy"),
                model=data.get("model", "gpt-4o-realtime-preview"),
                settings=self._parse_json_field(data.get("settings", {})),
                tags=self._parse_json_field(data.get("tags", []))
            )
            
            # Cache it
            if self.use_cache:
                self._cache[agent_id] = (config, datetime.now())
            
            logger.info(f"✅ Loaded: {config.name} ({config.category})")
            return config
        
        except Exception as e:
            logger.error(f"❌ Failed to load agent config: {e}", exc_info=True)
            return None
    
    def _parse_json_field(self, field: Any) -> Any:
        """Parse JSON field (handles both string and parsed formats)"""
        if isinstance(field, str):
            try:
                return json.loads(field)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON field: {field}")
                return field
        return field if field is not None else {}
    
    def clear_cache(self, agent_id: Optional[str] = None):
        """Clear cache for specific agent or all agents"""
        if agent_id:
            self._cache.pop(agent_id, None)
            logger.info(f"🗑️ Cleared cache for: {agent_id}")
        else:
            self._cache.clear()
            logger.info("🗑️ Cleared all cache")


# ============================================================================
# SPAWNER AGENT - Main orchestrator
# ============================================================================

class SpawnerAgent:
    """
    Single generic agent that:
    1. Extracts agent ID from room name
    2. Loads config from Supabase
    3. Morphs into that agent dynamically
    """
    
    def __init__(self):
        self.loader = AgentLoader()
    
    def extract_agent_id(self, room_name: str) -> Optional[str]:
        """
        Extract agent ID from room name
        
        Supported formats:
        - agent-{uuid}-{run_id}  (e.g., agent-550e8400-e29b-41d4-a716-446655440000-run123)
        - agent-{uuid}           (e.g., agent-550e8400-e29b-41d4-a716-446655440000)
        
        Returns:
            UUID string if valid format, None otherwise
        """
        patterns = [
            r"^agent-([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})-",
            r"^agent-([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, room_name)
            if match:
                return match.group(1)
        return None
    
    async def run_configured_agent(self, ctx: JobContext, config: AgentConfigData):
        """
        Run the dynamically configured agent
        This is the core: ONE agent deployment, MANY configurations
        """
        logger.info(f"🚀 Spawning agent: {config.name} (ID: {config.id})")
        logger.info(f"📝 Voice: {config.voice}, Model: {config.model}")
        logger.info(f"💬 Category: {config.category}")
        
        try:
            # Build instructions from config
            instructions = self._build_instructions(config)
            
            # Create the LLM with voice configuration
            model = openai.realtime.RealtimeModel(
                voice=config.voice,
                temperature=config.settings.get("temperature", 0.8),
                instructions=instructions,
            )
            
            # Connect to room
            await ctx.connect()
            logger.info(f"✅ Connected to room: {ctx.room.name}")
            
            # Create assistant with configured model
            assistant = agents.VoicePipelineAgent(
                vad=silero.VAD.load(),
                stt=openai.STT(),
                llm=model,
                tts=openai.TTS(voice=config.voice),
            )
            
            # Start the assistant
            assistant.start(ctx.room)
            logger.info(f"🎙️ Assistant started and listening...")
            
            # Wait for participant to join before greeting
            await self._wait_for_participant(ctx)
            
            # Initial greeting
            greeting = self._build_greeting(config)
            await assistant.say(greeting, allow_interruptions=True)
            
            # Keep agent alive - the assistant runs until room closes
            logger.info("✨ Agent is live and ready!")
            
        except Exception as e:
            logger.error(f"❌ Error running configured agent: {e}", exc_info=True)
            raise
    
    def _build_instructions(self, config: AgentConfigData) -> str:
        """
        Build complete instructions from config
        Priority: instructions_override > prompt_text > default
        """
        instructions = config.instructions_override or config.prompt_text
        
        if not instructions:
            # Fallback to basic instructions
            instructions = f"""You are {config.name}, a helpful AI assistant.
Category: {config.category}
Description: {config.tagline}

Be helpful, friendly, and professional."""
        
        # Add metadata context (helps agent understand itself)
        metadata = f"""

[Agent Metadata - Do not mention unless relevant]
- Name: {config.name}
- Category: {config.category}
- Tags: {', '.join(config.tags) if config.tags else 'general'}
"""
        
        return instructions + metadata
    
    def _build_greeting(self, config: AgentConfigData) -> str:
        """Build personalized greeting from config"""
        greeting = f"Hi! I'm {config.name}."
        
        if config.tagline:
            greeting += f" {config.tagline}"
        
        greeting += " How can I help you today?"
        
        return greeting
    
    async def _wait_for_participant(self, ctx: JobContext, timeout: float = 30.0):
        """Wait for a participant to join before greeting"""
        if len(ctx.room.remote_participants) > 0:
            return
        
        logger.info("⏳ Waiting for participant to join...")
        try:
            await asyncio.wait_for(
                self._participant_connected(ctx),
                timeout=timeout
            )
            logger.info("👤 Participant joined!")
            # Give them a moment to settle
            await asyncio.sleep(1)
        except asyncio.TimeoutError:
            logger.warning("⚠️ No participant joined within timeout")
    
    async def _participant_connected(self, ctx: JobContext):
        """Wait for participant connection event"""
        while len(ctx.room.remote_participants) == 0:
            await asyncio.sleep(0.1)


# ============================================================================
# ENTRYPOINT - Main function called by LiveKit
# ============================================================================

async def spawner_entrypoint(ctx: JobContext):
    """
    Main entry point - listens for agent-* rooms
    This is your ONLY deployed agent that handles ALL configurations
    
    Flow:
        1. Check if room matches pattern: agent-{uuid}-{run_id}
        2. Extract UUID from room name
        3. Load agent config from Supabase
        4. Spawn configured agent with those settings
        5. Keep agent alive until room closes
    """
    room_name = ctx.room.name
    logger.info(f"🔍 Spawner entrypoint called for room: {room_name}")
    
    # Only handle agent-* rooms
    if not room_name.startswith("agent-"):
        logger.warning(f"⚠️ Room '{room_name}' doesn't match agent-* pattern. Ignoring.")
        return
    
    # Extract agent ID
    spawner = SpawnerAgent()
    agent_id = spawner.extract_agent_id(room_name)
    
    if not agent_id:
        logger.error(f"❌ Could not extract valid UUID from room: {room_name}")
        await ctx.connect()
        await asyncio.sleep(1)
        # Optionally notify user of error
        return
    
    logger.info(f"🎯 Extracted agent ID: {agent_id}")
    
    # Load configuration from Supabase
    try:
        config = await spawner.loader.load_agent_config(agent_id)
        
        if not config:
            logger.error(f"❌ No configuration found for agent: {agent_id}")
            await ctx.connect()
            # Could say: "Sorry, this agent configuration couldn't be loaded"
            return
        
        logger.info(f"✅ Config loaded: {config.name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}", exc_info=True)
        return
    
    # Run the configured agent
    await spawner.run_configured_agent(ctx, config)


# ============================================================================
# MAIN - Entry point when running the file
# ============================================================================

if __name__ == "__main__":
    # Single deployment - handles all agent configurations
    logger.info("🚀 Starting Dynamic Agent Spawner...")
    logger.info("📋 Listening for rooms with pattern: agent-{uuid}-{run_id}")
    
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=spawner_entrypoint,
        )
    )