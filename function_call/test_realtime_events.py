"""
Test client for real-time agent creation communication
Tests WebSocket events and agent creation flow
"""

import asyncio
import socketio
import json
import time
from datetime import datetime

class AgentCreationTestClient:
    def __init__(self, server_url='http://localhost:5000'):
        self.sio = socketio.AsyncClient()
        self.server_url = server_url
        self.session_id = None
        self.events_received = []
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Set up WebSocket event handlers"""

        @self.sio.event
        async def connect():
            print("✅ Connected to server")

        @self.sio.event
        async def disconnect():
            print("❌ Disconnected from server")

        @self.sio.event
        async def connection_response(data):
            print(f"📡 Connection response: {data}")

        @self.sio.event
        async def agent_creation_update(data):
            """Handle real-time agent creation updates"""
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"🔄 [{timestamp}] {data['step']} - {data['status']}: {data['message']}")

            if data.get('error'):
                print(f"   ❌ Error: {data['error']}")

            if data.get('agent_name'):
                print(f"   🤖 Agent: {data['agent_name']}")

            if data.get('voice_model'):
                print(f"   🎵 Voice: {data['voice_model']}")

            # Store event for analysis
            self.events_received.append({
                'timestamp': timestamp,
                'data': data
            })

        @self.sio.event
        async def agent_creation_started(data):
            print(f"🚀 Agent creation started: {data}")
            self.session_id = data.get('session_id')

        @self.sio.event
        async def agent_creation_error(data):
            print(f"❌ Agent creation error: {data}")

    async def test_agent_creation_flow(self):
        """Test complete agent creation flow"""
        try:
            # Connect to server
            print("🔌 Connecting to server...")
            await self.sio.connect(self.server_url)
            await asyncio.sleep(1)

            # Test data
            test_requirements = {
                'business_name': 'Mario\'s Pizza Palace',
                'business_type': 'pizza restaurant',
                'target_audience': 'families and pizza lovers',
                'main_functions': ['take_order', 'menu_inquiry', 'store_hours'],
                'tone': 'friendly and enthusiastic'
            }

            # Start agent creation
            print("\n🎯 Starting agent creation test...")
            await self.sio.emit('start_agent_creation', {
                'session_id': f'test-{int(time.time())}',
                'requirements': test_requirements
            })

            # Wait for completion (up to 30 seconds)
            print("⏳ Waiting for agent creation to complete...")
            start_time = time.time()
            timeout = 30

            while time.time() - start_time < timeout:
                await asyncio.sleep(1)

                # Check if we received completion event
                for event in self.events_received:
                    if (event['data'].get('step') == 'overall' and
                        event['data'].get('status') in ['completed', 'failed']):
                        print(f"\n✅ Agent creation finished: {event['data']['status']}")
                        return True

            print("\n⏰ Test timed out")
            return False

        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        finally:
            await self.sio.disconnect()

    async def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            print("\n🧪 Testing error handling...")
            await self.sio.connect(self.server_url)
            await asyncio.sleep(1)

            # Send invalid data to trigger error
            await self.sio.emit('start_agent_creation', {
                'session_id': f'error-test-{int(time.time())}',
                'requirements': {}  # Empty requirements should trigger validation error
            })

            await asyncio.sleep(5)
            print("✅ Error handling test completed")

        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
        finally:
            await self.sio.disconnect()

    def print_event_summary(self):
        """Print summary of received events"""
        print(f"\n📊 Event Summary: {len(self.events_received)} events received")

        steps_seen = set()
        for event in self.events_received:
            step = event['data'].get('step', 'unknown')
            status = event['data'].get('status', 'unknown')
            steps_seen.add(f"{step}:{status}")

        print("📋 Steps and statuses seen:")
        for step_status in sorted(steps_seen):
            print(f"   • {step_status}")

async def run_tests():
    """Run all tests"""
    print("🧪 Starting Real-time Agent Creation Tests")
    print("=" * 50)

    client = AgentCreationTestClient()

    # Test 1: Normal agent creation flow
    print("\n1️⃣ Testing normal agent creation flow...")
    success = await client.test_agent_creation_flow()

    if success:
        client.print_event_summary()

    # Test 2: Error handling
    print("\n2️⃣ Testing error handling...")
    await client.test_error_handling()

    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    print("🚀 Real-time Agent Creation Test Client")
    print("📡 Make sure the webhook server is running on localhost:5000")
    print()

    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")