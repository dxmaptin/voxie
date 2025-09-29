#!/usr/bin/env python3
"""
Test script for bidirectional progress system
Tests the complete flow: production bridge → Railway → frontend + agent callbacks
"""

import asyncio
import sys
import os
import time
from typing import Optional

# Add the src directory to Python path
sys.path.append('/Users/dxma/Desktop/voxie-clean/voxie-test/src')

async def test_bidirectional_progress():
    """Test the complete bidirectional progress system"""

    print("🧪 Testing Bidirectional Agent Progress System")
    print("=" * 50)

    # Import modules
    try:
        from production_bridge import initialize_production_bridge
        from progress_templates import get_voice_announcement, should_announce_voice
        print("✅ Modules imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return

    # Initialize production bridge
    try:
        production_bridge = initialize_production_bridge()
        print("✅ Production bridge initialized")
    except Exception as e:
        print(f"❌ Production bridge initialization failed: {e}")
        return

    # Test session
    session_id = f"test_session_{int(time.time())}"
    print(f"🎯 Test session: {session_id}")

    # Mock agent callback to simulate VoxieAgent
    progress_updates = []

    async def mock_agent_callback(step_name: str, status: str, message: str):
        """Mock callback that simulates VoxieAgent receiving progress"""
        voice_msg = get_voice_announcement(step_name, status)
        should_announce = should_announce_voice(step_name, status)

        progress_updates.append({
            'step': step_name,
            'status': status,
            'message': message,
            'voice_message': voice_msg,
            'should_announce': should_announce
        })

        print(f"🤖 Voxie received: {step_name}:{status}")
        if should_announce:
            print(f"🎙️ Would announce: \"{voice_msg}\"")
        else:
            print(f"📝 Logged (not announced): {step_name}:{status}")

    # Register mock agent for callbacks
    try:
        production_bridge.register_agent_session(session_id, mock_agent_callback)
        print("✅ Mock agent registered for callbacks")
    except Exception as e:
        print(f"❌ Agent registration failed: {e}")
        return

    # Test the complete agent creation flow
    print("\n🚀 Simulating agent creation process...")
    print("-" * 30)

    test_steps = [
        ('scenario', 'started', 'Analyzing restaurant requirements...'),
        ('scenario', 'completed', 'Restaurant business type identified'),
        ('database_creation', 'started', 'Creating PostgreSQL database...'),
        ('database_creation', 'completed', 'Database created with 5 tables'),
        ('knowledge_base_setup', 'started', 'Connecting to Ragie knowledge base...'),
        ('knowledge_base_setup', 'completed', 'Knowledge base integration active'),
        ('voice', 'started', 'Setting up voice profile for "Mario\'s Pizza Assistant"...'),
        ('voice', 'completed', 'Voice profile configured - alloy voice'),
        ('prompts', 'started', 'Creating custom conversation prompts...'),
        ('prompts', 'completed', 'Conversation prompts configured'),
        ('overall', 'started', 'Finalizing agent configuration...'),
        ('overall', 'completed', 'Agent creation successful! Ready for deployment.')
    ]

    # Emit each step with delay to simulate real process
    for step_name, status, message in test_steps:
        print(f"\n📡 Emitting: {step_name}:{status}")
        production_bridge.emit_step(session_id, step_name, status, message)

        # Small delay to simulate processing time
        await asyncio.sleep(0.5)

    # Test cleanup
    try:
        production_bridge.unregister_agent_session(session_id)
        print("\n✅ Test session cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    # Report results
    print("\n📊 Test Results")
    print("=" * 30)
    print(f"✅ Total progress updates received: {len(progress_updates)}")

    announcements = [u for u in progress_updates if u['should_announce']]
    print(f"🎙️ Voice announcements triggered: {len(announcements)}")

    for update in announcements:
        print(f"   • {update['step']}:{update['status']} → \"{update['voice_message']}\"")

    print(f"\n📝 Total events logged: {len(progress_updates)}")
    print("✅ Bidirectional progress system test completed!")

    # Test Railway webhook connection
    print(f"\n🔗 Testing Railway webhook connection...")
    if production_bridge.test_connection():
        print("✅ Railway webhook server reachable")
    else:
        print("⚠️ Railway webhook server not reachable (normal for local testing)")

if __name__ == "__main__":
    asyncio.run(test_bidirectional_progress())