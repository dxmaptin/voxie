#!/usr/bin/env python3
"""
Test Console Integration
Simulates what happens when you speak to Voxie and ask it to create an agent
"""

import asyncio
import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
voxie_test_dir = current_dir.parent / 'voxie-test' / 'src'
sys.path.append(str(voxie_test_dir))

async def test_voxie_console_integration():
    """Test what happens when Voxie creates an agent via console"""

    print("🎤 Simulating Console Voice Interaction with Voxie")
    print("=" * 60)
    print("This simulates what you'll see when you run:")
    print("  uv run python src/agent.py console")
    print("And then speak to Voxie asking it to create an agent")
    print("=" * 60)

    try:
        # Import the agent system
        from agent import VoxieAgent, agent_manager
        from console_broadcaster import console_broadcaster

        print("✅ Voxie agent system loaded")

        # Create a Voxie agent instance
        voxie = VoxieAgent()

        print("\n🗣️ User says: 'Create a pizza restaurant agent called Mario's Pizza'")
        print("🤖 Voxie stores requirements and then calls finalize_requirements()")
        print("\n--- EXPECTED CONSOLE OUTPUT WHEN USING VOICE ---")
        print("=" * 50)

        # Simulate storing requirements (what happens when you speak)
        agent_manager.user_requirements.business_name = "Mario's Pizza"
        agent_manager.user_requirements.business_type = "pizza restaurant"
        agent_manager.user_requirements.tone = "friendly and enthusiastic"
        agent_manager.user_requirements.main_functions = ["take_order", "menu_inquiry"]

        # This is what gets called when Voxie decides to create the agent
        result = await voxie.finalize_requirements()

        print(f"\n🤖 Voxie responds: '{result}'")

        # Wait for agent creation to complete
        print("\n⏳ Waiting for agent creation to complete...")
        await asyncio.sleep(8)  # Give time for the full pipeline

        print("\n✅ This is what you'll see in your terminal when speaking to Voxie!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing Console Integration")
    print("This shows exactly what logs will appear when you speak to Voxie")
    print()

    success = asyncio.run(test_voxie_console_integration())

    if success:
        print("\n🎉 Console integration test completed!")
        print("\n📋 Next steps:")
        print("1. Run: cd /Users/dxma/Desktop/voxie-clean/voxie-test")
        print("2. Run: uv run python src/agent.py console")
        print("3. Speak to Voxie and ask it to create an agent")
        print("4. You should see the real-time logs in your terminal!")
    else:
        print("\n❌ Console integration test failed")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()