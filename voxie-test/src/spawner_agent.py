import logging
import re
from typing import Optional
from livekit import agents
from livekit.agents import JobContext, Agent, RoomInputOptions
from livekit.plugins import openai, noise_cancellation
from dotenv import load_dotenv
import asyncio
from agent_loader import AgentLoader, AgentConfigData
from dynamic_agent_factory import DynamicAgentFactory

load_dotenv(".env.local")
logger = logging.getLogger("spawner")


class SpawnerAgent:
    """Main spawner service"""
    
    def __init__(self):
        self.loader = AgentLoader()
    
    def extract_agent_id(self, room_name: str) -> Optional[str]:
        """
        Extract agent ID from room name
        Room format: agent-{agent_id}-{run_id}
        Example: agent-550e8400-e29b-41d4-a716-446655440000-run123
        
        Returns just the UUID part
        """
        pattern = r"^agent-([a-f0-9\-]+)-"
        match = re.match(pattern, room_name)
        if match:
            return match.group(1)
        return None
    
    async def run_demo(self, ctx: JobContext, config: AgentConfigData):
        """Run the demo agent in the spawned room"""
        logger.info(f"Starting demo for agent: {config.name}")
        
        try:
            # Create agent from config
            demo_agent = DynamicAgentFactory.create_agent(config)
            
            # Create session with agent's configured voice
            logger.info(f"Creating session with voice: {config.voice}, model: {config.model}")
            
            # Create RealtimeModel with voice parameter
            llm = openai.realtime.RealtimeModel(voice=config.voice)
            
            session = agents.AgentSession(llm=llm)
            
            # Start session - THIS KEEPS IT ALIVE
            logger.info("Starting agent session...")
            await session.start(
                room=ctx.room,
                agent=demo_agent,
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )
            
            # Wait a moment before agent introduces itself
            await asyncio.sleep(2)
            
            # Agent introduction
            greeting = f"Hello! I'm {config.name}. {config.tagline}"
            
            logger.info(f"Agent introducing itself: {greeting}")
            await session.generate_reply(
                instructions=f"Greet the user warmly. Say: \"{greeting}\" Then briefly explain how you can help them."
            )
            
            # KEEP SESSION ALIVE - The session.start() above runs the agent in the background
            # We need to keep this coroutine alive while the session is active
            logger.info("Agent session started. Listening for user input...")
            
            # The session runs indefinitely until the room closes or user disconnects
            # session.start() is awaited above, so we just wait for natural completion
            # The while True loop isn't needed - session.start() blocks until room closes
            logger.info("Agent is now active and listening for user input")
            
        except Exception as e:
            logger.error(f"Error running demo: {e}")
            raise


async def spawner_entrypoint(ctx: JobContext):
    """
    Main entry point for spawner
    Listens only for rooms matching agent-* pattern
    """
    room_name = ctx.room.name
    logger.info(f"Spawner entrypoint called for room: {room_name}")
    
    # Check if this is an agent-* room
    if not room_name.startswith("agent-"):
        logger.warning(f"Room '{room_name}' does not match agent-* pattern. Skipping.")
        return
    
    # Extract agent ID from room name
    spawner = SpawnerAgent()
    agent_id = spawner.extract_agent_id(room_name)
    
    if not agent_id:
        logger.error(f"Could not extract agent ID from room: {room_name}")
        return
    
    logger.info(f"Extracted agent ID: {agent_id}")
    
    # Load agent configuration from Supabase
    config = await spawner.loader.load_agent_config(agent_id)
    
    if not config:
        logger.error(f"Failed to load config for agent: {agent_id}")
        return
    
    logger.info(f"Loaded config successfully. Running demo...")
    
    # Run the demo agent
    await spawner.run_demo(ctx, config)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=spawner_entrypoint))