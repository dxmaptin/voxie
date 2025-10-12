"""
Simple Agent Runner - Production-Ready Single Process Agent
Supports both dev mode (auto-join rooms) and production mode (specific room)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add paths for imports
sys.path.append('./voxie-test/src')
sys.path.append('./function_call')

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import openai, noise_cancellation

# Import agent components
from agent import (
    agent_manager,
    DemoAgentCreator,
    UserRequirements,
    ProcessedAgentSpec,
    AgentState,
    CallAnalytics,
    TranscriptionHandler
)
from agent_persistence import AgentPersistence

load_dotenv(".env.local")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple-agent")


async def run_specific_agent(agent_id: str, room_name: str):
    """
    Production mode: Connect specific agent to specific room
    This runs as a single process and exits when done
    """
    logger.info(f"🚀 Starting agent {agent_id} for room {room_name}")

    try:
        # Load agent configuration from database
        logger.info(f"📥 Loading agent configuration: {agent_id}")
        agent_data = AgentPersistence.load_agent_config(agent_id)

        if not agent_data:
            logger.error(f"❌ Agent not found: {agent_id}")
            sys.exit(1)

        # Extract configuration
        user_req_dict = agent_data.get('user_requirements', {})
        processed_spec_dict = agent_data.get('processed_spec', {})

        logger.info(f"✅ Loaded: {processed_spec_dict.get('agent_type')}")
        logger.info(f"🎵 Voice: {processed_spec_dict.get('voice')}")
        logger.info(f"🏢 Business: {user_req_dict.get('business_name')}")

        # Convert to dataclasses
        agent_manager.user_requirements = UserRequirements(
            business_type=user_req_dict.get('business_type'),
            business_name=user_req_dict.get('business_name'),
            target_audience=user_req_dict.get('target_audience'),
            main_functions=user_req_dict.get('main_functions', []),
            tone=user_req_dict.get('tone'),
            special_requirements=user_req_dict.get('special_requirements', []),
            contact_info=user_req_dict.get('contact_info', {})
        )

        agent_manager.processed_spec = ProcessedAgentSpec(
            agent_type=processed_spec_dict.get('agent_type', 'Custom Agent'),
            instructions=processed_spec_dict.get('instructions', ''),
            voice=processed_spec_dict.get('voice', 'alloy'),
            functions=processed_spec_dict.get('functions', []),
            sample_responses=processed_spec_dict.get('sample_responses', []),
            business_context=processed_spec_dict.get('business_context', {})
        )

        agent_manager.current_agent_id = agent_id
        agent_manager.state = AgentState.DEMO_ACTIVE

        # Initialize analytics
        import uuid
        session_id = f"{room_name}_{uuid.uuid4().hex[:8]}"

        agent_manager.analytics = CallAnalytics(
            session_id=session_id,
            agent_id=agent_id,
            customer_phone=None
        )

        await agent_manager.analytics.start_call(
            room_name=room_name,
            primary_agent_type=agent_manager.processed_spec.agent_type
        )
        logger.info(f"📊 Analytics started: {session_id}")

        # Initialize transcription
        agent_manager.transcription = TranscriptionHandler(analytics=agent_manager.analytics)
        logger.info("🎙️ Transcription handler initialized")

        # Create demo agent
        logger.info(f"🏗️ Creating agent instance...")
        demo_agent = DemoAgentCreator.create_agent(agent_manager.processed_spec)
        logger.info("✅ Agent created")

        # Connect to LiveKit room directly
        logger.info(f"🔗 Connecting to room: {room_name}")

        # Use LiveKit RTC to connect directly
        from livekit import rtc

        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, livekit_api_key, livekit_api_secret]):
            raise ValueError("Missing LiveKit configuration in environment")

        # Generate access token for the agent
        from livekit import api
        token = api.AccessToken(livekit_api_key, livekit_api_secret)
        token.with_identity(f"agent-{agent_id[:8]}")
        token.with_name(f"Agent-{agent_manager.processed_spec.agent_type}")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True
        ))
        jwt_token = token.to_jwt()

        # Create room connection
        room_instance = rtc.Room()

        # Connect to room
        await room_instance.connect(livekit_url, jwt_token)
        logger.info(f"✅ Connected to room: {room_name}")

        # Store room reference
        agent_manager.room = room_instance

        # Start agent session
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(voice=agent_manager.processed_spec.voice)
        )

        agent_manager.current_session = session

        await session.start(
            room=room_instance,
            agent=demo_agent,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )

        logger.info("✅ Agent session started")

        # Get greeting
        business_name = agent_manager.processed_spec.business_context.get("business_name", "our business")
        greeting = agent_manager.processed_spec.business_context.get("greeting")

        if greeting:
            logger.info(f"💬 Using custom greeting")
            await session.generate_reply(instructions=f"Say this exact greeting: {greeting}")
        else:
            logger.info(f"💬 Using default greeting")
            await session.generate_reply(
                instructions=f"Greet the user warmly as the {agent_manager.processed_spec.agent_type} for {business_name}. Introduce yourself and ask how you can help them today."
            )

        logger.info(f"🎉 {agent_manager.processed_spec.agent_type} is now active!")

        # Keep running until room ends or becomes empty
        try:
            while room_instance.connection_state == rtc.ConnectionState.CONN_CONNECTED:
                # Check if room is empty (no remote participants)
                num_participants = len(room_instance.remote_participants)
                if num_participants == 0:
                    logger.info(f"🏃 Room empty ({num_participants} participants), exiting...")
                    break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in room monitor loop: {e}")

        logger.info("🔌 Room disconnected, shutting down...")

        # Explicitly disconnect
        await room_instance.disconnect()
        await session.aclose()

        logger.info("✅ Agent process exiting cleanly")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Failed to run agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


async def entrypoint_dev(ctx: agents.JobContext):
    """
    Dev mode entrypoint: Auto-join any new room
    Uses agent_id from environment if set, otherwise defaults to Voxie
    """
    agent_id = os.getenv("AGENT_ID")

    if agent_id:
        logger.info(f"🎯 Dev mode with specific agent: {agent_id}")
        # Use the same logic as production but in dev mode
        await run_specific_agent_in_context(ctx, agent_id)
    else:
        logger.info("🎯 Dev mode with Voxie (default)")
        # Import and run original Voxie entrypoint
        from agent import entrypoint as voxie_entrypoint
        await voxie_entrypoint(ctx)


async def run_specific_agent_in_context(ctx: agents.JobContext, agent_id: str):
    """Run specific agent within a JobContext (for dev mode)"""
    # Same logic as run_specific_agent but uses provided ctx
    logger.info(f"📥 Loading agent configuration: {agent_id}")
    agent_data = AgentPersistence.load_agent_config(agent_id)

    if not agent_data:
        logger.error(f"❌ Agent not found: {agent_id}")
        return

    # Extract configuration
    user_req_dict = agent_data.get('user_requirements', {})
    processed_spec_dict = agent_data.get('processed_spec', {})

    logger.info(f"✅ Loaded: {processed_spec_dict.get('agent_type')}")

    # Convert to dataclasses
    agent_manager.user_requirements = UserRequirements(
        business_type=user_req_dict.get('business_type'),
        business_name=user_req_dict.get('business_name'),
        target_audience=user_req_dict.get('target_audience'),
        main_functions=user_req_dict.get('main_functions', []),
        tone=user_req_dict.get('tone'),
        special_requirements=user_req_dict.get('special_requirements', []),
        contact_info=user_req_dict.get('contact_info', {})
    )

    agent_manager.processed_spec = ProcessedAgentSpec(
        agent_type=processed_spec_dict.get('agent_type', 'Custom Agent'),
        instructions=processed_spec_dict.get('instructions', ''),
        voice=processed_spec_dict.get('voice', 'alloy'),
        functions=processed_spec_dict.get('functions', []),
        sample_responses=processed_spec_dict.get('sample_responses', []),
        business_context=processed_spec_dict.get('business_context', {})
    )

    agent_manager.current_agent_id = agent_id
    agent_manager.state = AgentState.DEMO_ACTIVE
    agent_manager.room = ctx.room
    agent_manager.context = ctx

    # Initialize analytics
    import uuid
    session_id = f"{ctx.room.name}_{uuid.uuid4().hex[:8]}"

    agent_manager.analytics = CallAnalytics(
        session_id=session_id,
        agent_id=agent_id,
        customer_phone=None
    )

    await agent_manager.analytics.start_call(
        room_name=ctx.room.name,
        primary_agent_type=agent_manager.processed_spec.agent_type
    )

    # Initialize transcription
    agent_manager.transcription = TranscriptionHandler(analytics=agent_manager.analytics)

    # Create and start agent
    demo_agent = DemoAgentCreator.create_agent(agent_manager.processed_spec)

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice=agent_manager.processed_spec.voice)
    )

    agent_manager.current_session = session

    await session.start(
        room=ctx.room,
        agent=demo_agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Generate greeting
    business_name = agent_manager.processed_spec.business_context.get("business_name", "our business")
    greeting = agent_manager.processed_spec.business_context.get("greeting")

    if greeting:
        await session.generate_reply(instructions=f"Say this exact greeting: {greeting}")
    else:
        await session.generate_reply(
            instructions=f"Greet the user warmly as the {agent_manager.processed_spec.agent_type} for {business_name}. Introduce yourself and ask how you can help them today."
        )

    logger.info(f"🎉 {agent_manager.processed_spec.agent_type} is now active in dev mode!")


if __name__ == "__main__":
    # Check if running in dev mode or production mode
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        # DEV MODE: Auto-join any new room (for local testing)
        logger.info("🔧 Starting in DEV mode (auto-join rooms)")
        agents.cli.run_app(
            agents.WorkerOptions(
                entrypoint_fnc=entrypoint_dev,
                num_idle_processes=0  # Still avoid pre-spawning
            )
        )
    else:
        # PRODUCTION MODE: Connect to specific room
        logger.info("🚀 Starting in PRODUCTION mode (specific room)")

        # Get required environment variables
        agent_id = os.getenv("AGENT_ID")
        room_name = os.getenv("ROOM_NAME")

        if not agent_id or not room_name:
            logger.error("❌ Missing required environment variables:")
            logger.error("   AGENT_ID: Agent ID to load from database")
            logger.error("   ROOM_NAME: LiveKit room to connect to")
            logger.error("\nUsage:")
            logger.error("   Production: AGENT_ID=xyz ROOM_NAME=room-123 python simple_agent.py")
            logger.error("   Dev mode:   AGENT_ID=xyz python simple_agent.py dev")
            sys.exit(1)

        # Run the agent
        asyncio.run(run_specific_agent(agent_id, room_name))
