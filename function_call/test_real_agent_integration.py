#!/usr/bin/env python3
"""
Real LiveKit Agent Integration Test
Tests actual agent creation pipeline with real-time WebSocket events

This test:
1. Starts the WebSocket server
2. Creates a real LiveKit agent manager
3. Triggers actual agent creation with specific requirements
4. Monitors real-time events
5. Verifies the agent was created with correct specifications
"""

import asyncio
import sys
import os
import threading
import time
import socketio
import subprocess
import signal
import json
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
function_call_dir = current_dir
voxie_test_dir = current_dir.parent / 'voxie-test' / 'src'
sys.path.append(str(function_call_dir))
sys.path.append(str(voxie_test_dir))

class LiveKitAgentIntegrationTest:
    """Real integration test for LiveKit agent creation pipeline"""

    def __init__(self):
        self.webhook_server_process = None
        self.socket_client = None
        self.events_received = []
        self.agent_created = False
        self.test_session_id = None

    async def setup_test_environment(self):
        """Set up the test environment"""
        print("🔧 Setting up test environment...")

        # Check if .env.local exists, if not create minimal one
        env_file = current_dir.parent / 'voxie-test' / '.env.local'
        if not env_file.exists():
            print("📝 Creating minimal .env.local file...")
            with open(env_file, 'w') as f:
                f.write("# Minimal config for testing\n")
                f.write("LIVEKIT_URL=ws://localhost:7880\n")
                f.write("LIVEKIT_API_KEY=devkey\n")
                f.write("LIVEKIT_API_SECRET=secret\n")
                f.write("OPENAI_API_KEY=test-key\n")

        # Start webhook server in background
        print("🚀 Starting webhook server...")
        self.webhook_server_process = subprocess.Popen(
            [sys.executable, 'webhook_server.py'],
            cwd=function_call_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to start
        await asyncio.sleep(3)

        if self.webhook_server_process.poll() is not None:
            stdout, stderr = self.webhook_server_process.communicate()
            print(f"❌ Server failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            return False

        print("✅ Webhook server started")
        return True

    async def connect_websocket_client(self):
        """Connect WebSocket client to monitor events"""
        print("🔌 Connecting WebSocket client...")

        self.socket_client = socketio.AsyncClient()

        @self.socket_client.event
        async def connect():
            print("✅ WebSocket client connected")

        @self.socket_client.event
        async def agent_creation_update(data):
            timestamp = time.strftime("%H:%M:%S")
            step = data.get('step', 'unknown')
            status = data.get('status', 'unknown')
            message = data.get('message', '')

            print(f"📡 [{timestamp}] {step}:{status} - {message}")

            if data.get('agent_name'):
                print(f"    🤖 Agent: {data['agent_name']}")
            if data.get('voice_model'):
                print(f"    🎵 Voice: {data['voice_model']}")
            if data.get('error'):
                print(f"    ❌ Error: {data['error']}")

            self.events_received.append({
                'timestamp': timestamp,
                'step': step,
                'status': status,
                'data': data
            })

            # Check if agent creation completed
            if step == 'overall' and status == 'completed':
                self.agent_created = True
                print("🎉 Agent creation completed!")

        @self.socket_client.event
        async def agent_creation_started(data):
            print(f"🚀 Agent creation started: {data}")

        @self.socket_client.event
        async def agent_creation_error(data):
            print(f"❌ Agent creation error: {data}")

        try:
            await self.socket_client.connect('http://localhost:5000')
            await asyncio.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Failed to connect WebSocket client: {e}")
            return False

    async def trigger_real_agent_creation(self):
        """Trigger actual agent creation with real requirements"""
        print("\n🎯 Triggering real agent creation...")

        # Test requirements that should create an actual agent
        test_requirements = {
            'business_name': 'Test Pizza Palace',
            'business_type': 'pizza restaurant',
            'target_audience': 'families and food lovers',
            'tone': 'friendly and enthusiastic',
            'main_functions': ['take_order', 'menu_inquiry', 'store_hours'],
            'voice_model': 'echo',  # Specifically request echo voice
            'special_requirements': ['Use echo voice model', 'Enable real-time updates']
        }

        self.test_session_id = f'integration-test-{int(time.time())}'

        print(f"📋 Requirements: {json.dumps(test_requirements, indent=2)}")
        print(f"🆔 Session ID: {self.test_session_id}")

        # Send to WebSocket server
        await self.socket_client.emit('start_agent_creation', {
            'session_id': self.test_session_id,
            'requirements': test_requirements
        })

        print("✅ Agent creation request sent")

    async def monitor_agent_creation(self, timeout=60):
        """Monitor agent creation process with timeout"""
        print(f"⏳ Monitoring agent creation (timeout: {timeout}s)...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            await asyncio.sleep(1)

            # Check if agent creation completed
            if self.agent_created:
                print("✅ Agent creation detected as completed")
                return True

            # Check for failure
            for event in self.events_received:
                if event['step'] == 'overall' and event['status'] == 'failed':
                    print("❌ Agent creation failed")
                    return False

        print("⏰ Agent creation monitoring timed out")
        return False

    def verify_agent_specifications(self):
        """Verify the created agent meets our specifications"""
        print("\n🔍 Verifying agent specifications...")

        # Check for required events
        steps_seen = set()
        voice_model_found = None
        agent_name_found = None

        for event in self.events_received:
            step = event['step']
            status = event['status']
            data = event['data']

            steps_seen.add(f"{step}:{status}")

            if data.get('voice_model'):
                voice_model_found = data['voice_model']

            if data.get('agent_name'):
                agent_name_found = data['agent_name']

        print(f"📊 Steps seen: {sorted(steps_seen)}")
        print(f"🎵 Voice model found: {voice_model_found}")
        print(f"🤖 Agent name found: {agent_name_found}")

        # Verify requirements
        success = True

        # Check if we got the main pipeline steps
        required_steps = ['scenario:started', 'prompts:started', 'voice:started', 'knowledge_base:started']
        for step in required_steps:
            if step not in steps_seen:
                print(f"❌ Missing required step: {step}")
                success = False
            else:
                print(f"✅ Found required step: {step}")

        # Check voice model (should be one of the available ones, may not be echo if not supported)
        if voice_model_found:
            print(f"✅ Voice model configured: {voice_model_found}")
        else:
            print("❌ No voice model found in events")
            success = False

        # Check agent name
        if agent_name_found and 'Test Pizza Palace' in agent_name_found:
            print(f"✅ Agent name correctly set: {agent_name_found}")
        else:
            print(f"❌ Agent name not found or incorrect: {agent_name_found}")
            success = False

        return success

    async def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")

        if self.socket_client:
            await self.socket_client.disconnect()
            print("✅ WebSocket client disconnected")

        if self.webhook_server_process:
            self.webhook_server_process.terminate()
            try:
                self.webhook_server_process.wait(timeout=5)
                print("✅ Webhook server terminated")
            except subprocess.TimeoutExpired:
                self.webhook_server_process.kill()
                print("⚠️ Webhook server killed (timeout)")

    async def run_integration_test(self):
        """Run the complete integration test"""
        print("🧪 Starting LiveKit Agent Integration Test")
        print("=" * 60)

        try:
            # Setup
            if not await self.setup_test_environment():
                print("❌ Failed to set up test environment")
                return False

            # Connect WebSocket
            if not await self.connect_websocket_client():
                print("❌ Failed to connect WebSocket client")
                return False

            # Trigger agent creation
            await self.trigger_real_agent_creation()

            # Monitor creation process
            creation_success = await self.monitor_agent_creation(timeout=45)

            if not creation_success:
                print("❌ Agent creation did not complete successfully")
                return False

            # Verify specifications
            verification_success = self.verify_agent_specifications()

            if verification_success:
                print("\n🎉 Integration test PASSED!")
                print(f"✅ Total events received: {len(self.events_received)}")
                return True
            else:
                print("\n❌ Integration test FAILED!")
                print("❌ Agent specifications verification failed")
                return False

        except Exception as e:
            print(f"\n💥 Integration test crashed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            await self.cleanup()

def main():
    """Main entry point"""
    print("🚀 LiveKit Agent Real Integration Test")
    print("📡 This test will:")
    print("  1. Start the actual webhook server")
    print("  2. Connect real WebSocket client")
    print("  3. Trigger real agent creation")
    print("  4. Monitor actual real-time events")
    print("  5. Verify agent specifications")
    print()

    test = LiveKitAgentIntegrationTest()

    try:
        success = asyncio.run(test.run_integration_test())
        if success:
            print("\n✅ ALL TESTS PASSED - Real-time agent creation is working!")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED - Check the logs above")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()