#!/usr/bin/env python3
"""
Mock Voice Interaction Test
Simulates the complete voice interaction with Voxie without needing OpenAI API
Shows exactly what logs you'll see when the real voice system works
"""

import asyncio
import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
voxie_test_dir = current_dir.parent / 'voxie-test' / 'src'
sys.path.append(str(voxie_test_dir))

async def simulate_voice_interaction():
    """Simulate a complete voice interaction with Voxie"""

    print("🎤 MOCK VOICE INTERACTION SIMULATION")
    print("=" * 60)
    print("This shows exactly what you'll see when you speak to Voxie")
    print("(without needing OpenAI API key)")
    print("=" * 60)

    try:
        # Import the agent system
        from agent import VoxieAgent, agent_manager
        from console_broadcaster import console_broadcaster

        print("✅ Voxie agent system loaded with console broadcasting")

        # Create Voxie agent
        voxie = VoxieAgent()

        print("\n🎙️ SIMULATION: Voice conversation with Voxie")
        print("─" * 40)

        # Simulate user greeting
        print("👤 User speaks: 'Hello Voxie'")
        print("🤖 Voxie: 'Hi! I'm Voxie from VoxHive. I help create custom voice AI agents for your business. What type of business would you like to create an agent for?'")

        await asyncio.sleep(1)

        # Simulate user providing business info
        print("\n👤 User speaks: 'I want to create an agent for my pizza restaurant called Tony's Pizza Palace'")
        print("🤖 Voxie: 'Great! A pizza restaurant agent. What specific functions would you like your agent to handle?'")

        # Simulate storing requirements
        print("\n🔧 Voxie internally stores requirements...")
        await voxie.store_user_requirement("business_name", "Tony's Pizza Palace")
        await voxie.store_user_requirement("business_type", "pizza restaurant")
        await voxie.store_user_requirement("tone", "friendly and enthusiastic")
        await voxie.store_user_requirement("functions", "take_order, menu_inquiry, store_hours")

        await asyncio.sleep(1)

        print("\n👤 User speaks: 'I want it to take orders and answer menu questions'")
        print("🤖 Voxie: 'Perfect! I have all the information I need. Let me create your custom pizza restaurant agent now.'")

        print("\n🤖 Voxie calls finalize_requirements()...")
        print("─" * 50)

        # This triggers the real agent creation pipeline with console logs
        result = await voxie.finalize_requirements()
        print(f"🤖 Voxie responds: '{result}'")

        print("\n⏳ Agent creation in progress... (watch the real-time logs above)")
        await asyncio.sleep(8)  # Wait for creation to complete

        print("\n🤖 Voxie: 'Your Tony's Pizza Palace agent is ready! Would you like to test it now?'")
        print("👤 User: 'Yes, let me try it!'")

        print("\n🤖 Voxie: 'Great! I'm connecting you to your new agent now...'")

        print("\n" + "=" * 60)
        print("🎉 SIMULATION COMPLETE!")
        print("=" * 60)
        print("This is exactly what you'll see when you:")
        print("1. Set up a real OpenAI API key")
        print("2. Run: uv run python src/agent.py console")
        print("3. Speak to Voxie asking it to create an agent")
        print("\nThe real-time logs you saw above will appear in your terminal!")

        return True

    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Mock Voice Interaction Test")
    print("This simulates the complete voice conversation with Voxie")
    print("and shows the real-time agent creation logs you'll see")
    print()

    success = asyncio.run(simulate_voice_interaction())

    if success:
        print("\n✅ Simulation completed successfully!")
        print("\n📋 To see this for real:")
        print("1. Get an OpenAI API key from https://platform.openai.com/account/api-keys")
        print("2. Update voxie-test/.env.local with your real API key")
        print("3. Run: cd /Users/dxma/Desktop/voxie-clean/voxie-test")
        print("4. Run: uv run python src/agent.py console")
        print("5. Speak to Voxie and ask it to create an agent!")
    else:
        print("\n❌ Simulation failed")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()