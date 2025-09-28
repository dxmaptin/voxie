#!/usr/bin/env python3
"""
Direct Agent Creation Test
Tests the agent creation pipeline directly without WebSocket layer
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

class DirectAgentCreationTest:
    """Test agent creation directly without WebSocket overhead"""

    def __init__(self):
        self.events_captured = []

    async def setup_environment(self):
        """Set up test environment"""
        print("🔧 Setting up direct test environment...")

        # Create minimal .env.local if needed
        env_file = current_dir.parent / 'voxie-test' / '.env.local'
        if not env_file.exists():
            print("📝 Creating minimal .env.local for testing...")
            with open(env_file, 'w') as f:
                f.write("# Test environment\n")
                f.write("OPENAI_API_KEY=test-key-for-local-testing\n")
                f.write("LIVEKIT_URL=ws://localhost:7880\n")
                f.write("LIVEKIT_API_KEY=devkey\n")
                f.write("LIVEKIT_API_SECRET=secret\n")

        return True

    async def test_direct_agent_creation(self):
        """Test agent creation directly"""
        try:
            print("📦 Importing agent modules...")

            # Import the agent modules
            from agent import (
                ProcessingAgent, AgentManager, UserRequirements,
                ProcessedAgentSpec, AgentState
            )
            from event_broadcaster import AgentCreationEventBroadcaster

            print("✅ Agent modules imported successfully")

            # Create mock event broadcaster to capture events
            class MockEventBroadcaster:
                def __init__(self):
                    self.events = []

                def emit_step(self, session_id, step_name, status, message, error=None, **extra_data):
                    event = {
                        'session_id': session_id,
                        'step': step_name,
                        'status': status,
                        'message': message,
                        'error': error,
                        **extra_data
                    }
                    self.events.append(event)
                    print(f"📡 EVENT: {step_name}:{status} - {message}")
                    if extra_data:
                        for key, value in extra_data.items():
                            print(f"    {key}: {value}")

                def emit_overall_status(self, session_id, status, message, error=None, **extra_data):
                    self.emit_step(session_id, 'overall', status, message, error, **extra_data)

            # Create test requirements
            print("\n🎯 Creating test requirements...")
            requirements = UserRequirements()
            requirements.business_name = "Test Echo Pizza"
            requirements.business_type = "pizza restaurant"
            requirements.target_audience = "families"
            requirements.tone = "friendly and enthusiastic"
            requirements.main_functions = ["take_order", "menu_inquiry"]

            print(f"📋 Business: {requirements.business_name}")
            print(f"📋 Type: {requirements.business_type}")
            print(f"📋 Functions: {requirements.main_functions}")

            # Create event broadcaster
            mock_broadcaster = MockEventBroadcaster()

            # Create processing agent with event broadcaster
            print("\n🏗️ Creating ProcessingAgent...")
            processing_agent = ProcessingAgent(event_broadcaster=mock_broadcaster)

            # Test the processing pipeline
            print("\n⚡ Running agent creation pipeline...")
            session_id = "direct-test-session"

            try:
                spec = await processing_agent.process_requirements(requirements, session_id)
                print(f"\n✅ Agent created successfully!")
                print(f"🤖 Agent Type: {spec.agent_type}")
                print(f"🎵 Voice: {spec.voice}")
                print(f"🛠️ Functions: {len(spec.functions)} configured")
                print(f"💬 Sample Response: {spec.sample_responses[0]}")

                # Verify voice model
                if 'echo' in spec.voice:
                    print("✅ Echo voice model requested - using available voice")
                else:
                    print(f"ℹ️ Using available voice model: {spec.voice}")

                return True, mock_broadcaster.events, spec

            except Exception as e:
                print(f"❌ Agent creation failed: {e}")
                import traceback
                traceback.print_exc()
                return False, mock_broadcaster.events, None

        except ImportError as e:
            print(f"❌ Failed to import agent modules: {e}")
            print("ℹ️ This might be due to missing LiveKit dependencies")
            return False, [], None

    async def test_agent_manager_integration(self):
        """Test AgentManager integration"""
        try:
            print("\n🔧 Testing AgentManager integration...")

            from agent import AgentManager, UserRequirements
            from event_broadcaster import AgentCreationEventBroadcaster

            # Create mock socketio for broadcaster
            class MockSocketIO:
                def emit(self, event, data, room=None):
                    print(f"📡 SOCKETIO: {event} -> {data}")

            mock_socketio = MockSocketIO()

            # Create real event broadcaster
            from event_broadcaster import initialize_broadcaster
            broadcaster = initialize_broadcaster(mock_socketio)

            # Create agent manager
            agent_manager = AgentManager(event_broadcaster=broadcaster)

            # Set up requirements
            agent_manager.user_requirements.business_name = "Manager Test Pizza"
            agent_manager.user_requirements.business_type = "pizza"
            agent_manager.user_requirements.tone = "casual"

            print("🚀 Testing transition_to_processing...")

            # Test the transition (this should trigger the full pipeline)
            try:
                await agent_manager.transition_to_processing("manager-test-session")
                print("✅ AgentManager processing completed")
                return True
            except Exception as e:
                print(f"❌ AgentManager processing failed: {e}")
                return False

        except Exception as e:
            print(f"❌ AgentManager test failed: {e}")
            return False

    async def run_direct_tests(self):
        """Run all direct tests"""
        print("🧪 Direct Agent Creation Tests")
        print("=" * 50)

        if not await self.setup_environment():
            print("❌ Environment setup failed")
            return False

        # Test 1: Direct agent creation
        print("\n1️⃣ Testing direct agent creation...")
        success1, events, spec = await self.test_direct_agent_creation()

        if success1:
            print(f"\n📊 Events captured: {len(events)}")
            for event in events:
                print(f"  • {event['step']}:{event['status']} - {event['message']}")

            # Verify key events
            event_steps = [f"{e['step']}:{e['status']}" for e in events]
            required_events = ['scenario:started', 'prompts:started', 'voice:started']

            for req_event in required_events:
                if req_event in event_steps:
                    print(f"✅ Required event found: {req_event}")
                else:
                    print(f"❌ Missing required event: {req_event}")
                    success1 = False

        # Test 2: AgentManager integration
        print("\n2️⃣ Testing AgentManager integration...")
        success2 = await self.test_agent_manager_integration()

        # Results
        print("\n" + "=" * 50)
        if success1 and success2:
            print("🎉 ALL DIRECT TESTS PASSED!")
            print("✅ Agent creation pipeline is working")
            print("✅ Real-time events are being generated")
            print("✅ AgentManager integration is functional")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            print(f"❌ Direct creation: {'✅' if success1 else '❌'}")
            print(f"❌ Manager integration: {'✅' if success2 else '❌'}")
            return False

def main():
    """Main entry point"""
    print("🚀 Direct Agent Creation Test")
    print("📋 This test directly invokes the agent creation pipeline")
    print("🔍 It verifies that real-time events are generated")
    print()

    test = DirectAgentCreationTest()

    try:
        success = asyncio.run(test.run_direct_tests())
        if success:
            print("\n✅ DIRECT TESTS PASSED!")
            sys.exit(0)
        else:
            print("\n❌ DIRECT TESTS FAILED!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()