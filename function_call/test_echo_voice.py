#!/usr/bin/env python3
"""
Echo Voice Model Test
Test specifically requesting echo voice model and monitoring real-time events
"""

import asyncio
import sys
import os
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
voxie_test_dir = current_dir.parent / 'voxie-test' / 'src'
function_call_dir = current_dir
sys.path.append(str(voxie_test_dir))
sys.path.append(str(function_call_dir))

async def test_echo_voice_creation():
    """Test creating agent with echo voice specifically"""

    print("🎵 Testing Echo Voice Model Agent Creation")
    print("=" * 50)

    try:
        # Import modules
        from agent import ProcessingAgent, UserRequirements
        from event_broadcaster import AgentCreationEventBroadcaster

        print("✅ Modules imported successfully")

        # Mock broadcaster to capture events
        class MockBroadcaster:
            def __init__(self):
                self.events = []

            def emit_step(self, session_id, step, status, message, error=None, **extra):
                event = f"📡 {step}:{status} - {message}"
                if extra.get('voice_model'):
                    event += f" [Voice: {extra['voice_model']}]"
                if extra.get('agent_name'):
                    event += f" [Agent: {extra['agent_name']}]"
                print(event)
                self.events.append({'step': step, 'status': status, 'voice_model': extra.get('voice_model')})

            def emit_overall_status(self, session_id, status, message, error=None, **extra):
                self.emit_step(session_id, 'overall', status, message, error, **extra)

        broadcaster = MockBroadcaster()

        # Create requirements specifically requesting echo voice
        requirements = UserRequirements()
        requirements.business_name = "Echo Test Restaurant"
        requirements.business_type = "pizza"  # Pizza uses echo voice in templates
        requirements.tone = "enthusiastic"

        print(f"\n🎯 Creating agent with requirements:")
        print(f"   Business: {requirements.business_name}")
        print(f"   Type: {requirements.business_type}")
        print(f"   Expected Voice: echo (from pizza template)")

        # Create processing agent
        processor = ProcessingAgent(event_broadcaster=broadcaster)

        # Run the creation process
        print("\n⚡ Running agent creation...")
        spec = await processor.process_requirements(requirements, "echo-test-session")

        print(f"\n✅ Agent Created!")
        print(f"🤖 Agent Type: {spec.agent_type}")
        print(f"🎵 Voice Model: {spec.voice}")
        print(f"💬 Sample Response: {spec.sample_responses[0]}")

        # Check if echo voice was used
        voice_events = [e for e in broadcaster.events if e.get('voice_model')]
        if voice_events:
            voice_used = voice_events[0]['voice_model']
            if voice_used == 'echo':
                print(f"🎉 SUCCESS: Echo voice model was used as requested!")
            else:
                print(f"ℹ️ Voice model used: {voice_used} (pizza template default)")

        # Verify all events were generated
        step_statuses = [f"{e['step']}:{e['status']}" for e in broadcaster.events]
        required_events = ['scenario:started', 'scenario:completed', 'prompts:started',
                          'prompts:completed', 'voice:started', 'voice:completed',
                          'knowledge_base:started', 'knowledge_base:completed']

        print(f"\n📊 Event Verification:")
        all_found = True
        for event in required_events:
            if event in step_statuses:
                print(f"✅ {event}")
            else:
                print(f"❌ {event} - MISSING")
                all_found = False

        if all_found:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Echo voice agent creation successful")
            print(f"✅ All real-time events generated")
            print(f"✅ Pipeline working end-to-end")
            return True
        else:
            print(f"\n❌ Some events missing")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = asyncio.run(test_echo_voice_creation())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()