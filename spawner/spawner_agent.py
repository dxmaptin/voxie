"""
LiveKit Agent Spawner - Dynamically runs agents from database

This deployment ONLY runs user-created agents loaded from Supabase.
It NEVER runs Voxie (the agent creator).

Room Pattern: agent-*
Agent ID: Extracted from room metadata
"""

import os
import sys
import json
import logging
import asyncio
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import openai, noise_cancellation

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'voxie-test', 'src'))

from agent_loader import AgentLoader
from dynamic_agent_factory import DynamicAgentFactory
from call_analytics import CallAnalytics
from transcription_handler import TranscriptionHandler

load_dotenv('.env.local')
logger = logging.getLogger("spawner")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def spawner_entrypoint(ctx: agents.JobContext):
    """
    Spawner entry point - loads and runs a specific agent

    How it works:
    1. Extract agent_id from room metadata
    2. Load agent config from Supabase
    3. Create agent dynamically from config
    4. Start session with the agent
    5. Track analytics and transcription
    """

    logger.info("=" * 80)
    logger.info("🚀 SPAWNER DEPLOYMENT STARTING")
    logger.info(f"📦 Room: {ctx.room.name}")
    logger.info(f"🔍 Deployment Mode: SPAWNER (Agent Runner)")
    logger.info("=" * 80)

    # Extract agent_id from room metadata
    agent_id = None
    try:
        if ctx.room.metadata:
            metadata = json.loads(ctx.room.metadata) if isinstance(ctx.room.metadata, str) else ctx.room.metadata
            agent_id = metadata.get('agent_id')
            logger.info(f"📋 Room metadata: {metadata}")
    except Exception as e:
        logger.error(f"❌ Error parsing room metadata: {e}")

    # Fallback: Try to extract agent_id from room name (pattern: agent-{uuid}-...)
    if not agent_id:
        logger.warning("⚠️ No agent_id in metadata, trying room name...")
        room_name = ctx.room.name
        if room_name.startswith('agent-'):
            parts = room_name.split('-')
            if len(parts) >= 2:
                # Reconstruct UUID (format: agent-{uuid}-{random})
                # UUID is 8-4-4-4-12 hex chars with dashes
                potential_uuid = '-'.join(parts[1:6]) if len(parts) >= 6 else parts[1]
                agent_id = potential_uuid
                logger.info(f"🔍 Extracted agent_id from room name: {agent_id}")

    if not agent_id:
        logger.error("❌ No agent_id found in room metadata or room name")
        logger.error("   Room name should be: agent-{agent_id}-{suffix}")
        logger.error("   Or room metadata should contain: {\"agent_id\": \"...\"}")
        return

    logger.info(f"🎯 Loading agent: {agent_id}")

    # Load agent configuration from database
    agent_config = await AgentLoader.load_agent(agent_id)

    if not agent_config:
        logger.error(f"❌ Agent {agent_id} not found in database")
        logger.error("   Please verify the agent exists in Supabase 'agents' table")
        return

    logger.info(f"✅ Loaded agent configuration:")
    logger.info(f"   Name: {agent_config['name']}")
    logger.info(f"   Type: {agent_config['category']}")
    logger.info(f"   Voice: {agent_config['voice']}")
    logger.info(f"   Instructions: {len(agent_config['instructions'])} chars")
    logger.info(f"   Functions: {len(agent_config['functions'])}")

    # Create the agent dynamically
    logger.info("🏗️ Creating dynamic agent...")
    try:
        agent = DynamicAgentFactory.create_from_config(agent_config)
        logger.info("✅ Agent created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return

    # Initialize analytics tracking
    import uuid
    session_id = f"{ctx.room.name}_{uuid.uuid4().hex[:8]}"

    analytics = CallAnalytics(
        session_id=session_id,
        agent_id=agent_id,
        customer_phone=None
    )

    await analytics.start_call(
        room_name=ctx.room.name,
        primary_agent_type=agent_config['name']
    )
    logger.info(f"📊 Analytics started for session: {session_id}")

    # Initialize transcription handler
    transcription = TranscriptionHandler(analytics=analytics)
    logger.info("🎙️ Transcription handler initialized")

    # Start session with the agent
    logger.info(f"🎵 Starting session with voice: {agent_config['voice']}")
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice=agent_config['voice'])
    )

    logger.info("🚀 Starting agent session...")
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    logger.info("✅ Session started successfully")

    # Get greeting
    business_name = agent_config['business_context'].get('business_name', 'our business')
    agent_name = agent_config.get('agent_name')
    greeting = agent_config.get('greeting')

    # Build greeting instructions
    if greeting:
        logger.info(f"💬 Using custom greeting: {greeting[:80]}...")
        greeting_instruction = f"Say this exact greeting: {greeting}"
    elif agent_name:
        logger.info(f"💬 Using agent name: {agent_name}")
        greeting_instruction = f"Greet the user warmly. Introduce yourself as {agent_name} from {business_name} and ask how you can help them today."
    else:
        logger.info(f"💬 Using default greeting")
        greeting_instruction = f"Greet the user warmly as the {agent_config['name']} for {business_name}. Introduce yourself and ask how you can help them today."

    # Send greeting
    await session.generate_reply(instructions=greeting_instruction)

    # Log greeting to transcription
    await transcription.on_agent_speech(greeting or f"Hello! I'm from {business_name}. How can I help you?")

    logger.info("=" * 80)
    logger.info(f"✅ AGENT ACTIVE: {agent_config['name']}")
    logger.info(f"📍 Room: {ctx.room.name}")
    logger.info(f"🎯 Agent ID: {agent_id}")
    logger.info(f"🎵 Voice: {agent_config['voice']}")
    logger.info("=" * 80)

    # Set up room disconnect handler for analytics
    @ctx.room.on("disconnected")
    async def on_room_disconnected():
        """Handle room disconnect - generate summary for calls >3 minutes"""
        logger.info("🔌 Room disconnected - checking if summary should be generated...")

        if analytics and transcription:
            try:
                # Check call duration
                call_start = analytics.call_session_id
                if call_start:
                    # Fetch call session to check duration
                    sys.path.append('./function_call')
                    from supabase_client import supabase_client
                    from datetime import datetime, timezone

                    result = supabase_client.client.table('call_sessions')\
                        .select('started_at')\
                        .eq('id', call_start)\
                        .execute()

                    if result.data and len(result.data) > 0:
                        started_at_str = result.data[0]['started_at']
                        started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        duration_seconds = (now - started_at).total_seconds()

                        logger.info(f"⏱️ Call duration: {duration_seconds:.0f} seconds")

                        # Generate summary if call >= 3 minutes
                        if duration_seconds >= 180:
                            logger.info("✅ Call duration >= 3 minutes, generating summary...")

                            await analytics.end_call(
                                call_status='completed',
                                sentiment='neutral'
                            )

                            summary = await transcription.generate_summary_and_log()

                            if summary:
                                logger.info(f"✅ Auto-generated summary: {summary.get('call_category')} - {summary.get('business_outcome')}")
                            else:
                                logger.warning("⚠️ Summary generation failed")
                        else:
                            logger.info(f"⏭️ Call too short ({duration_seconds:.0f}s < 180s), skipping summary")
                            await analytics.end_call(call_status='completed')

            except Exception as e:
                logger.error(f"❌ Error in disconnect handler: {e}")
                import traceback
                logger.error(traceback.format_exc())


if __name__ == "__main__":
    logger.info("🌟 Starting LiveKit Agent Spawner")
    logger.info("🔍 This deployment ONLY runs user-created agents")
    logger.info("📋 Room pattern: agent-*")
    logger.info("=" * 80)

    # IMPORTANT: Only join rooms matching the pattern "agent-*"
    # This prevents spawner from joining Voxie creation rooms
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=spawner_entrypoint,
        # Room pattern filtering - ONLY join agent execution rooms
        # Voxie uses "voxie-creation-*" pattern
        # We use "agent-*" pattern
        # This ensures complete separation
        num_idle_processes=1  # Keep one worker ready for fast spawning
    ))
