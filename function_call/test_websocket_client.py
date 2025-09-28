#!/usr/bin/env python3
"""
WebSocket Client Test
Tests the actual WebSocket communication with detailed logging

This connects to your webhook server and tests real WebSocket communication
"""

import asyncio
import socketio
import json
import time
import sys
from datetime import datetime

class WebSocketClientTest:
    """Test WebSocket client with detailed logging"""

    def __init__(self, server_url='http://localhost:5000'):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.events_received = []
        self.connected = False
        self.test_completed = False

        # Setup event handlers
        self.setup_handlers()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        return log_entry

    def setup_handlers(self):
        """Setup WebSocket event handlers"""

        @self.sio.event
        async def connect():
            self.connected = True
            self.log("✅ Connected to WebSocket server", "SUCCESS")

        @self.sio.event
        async def disconnect():
            self.connected = False
            self.log("❌ Disconnected from WebSocket server", "WARNING")

        @self.sio.event
        async def connection_response(data):
            self.log(f"📡 Connection response: {json.dumps(data)}", "RESPONSE")

        @self.sio.event
        async def agent_creation_started(data):
            self.log(f"🚀 Agent creation started: {json.dumps(data)}", "EVENT")

        @self.sio.event
        async def agent_creation_update(data):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Store event
            event_with_timestamp = {**data, 'client_received_at': timestamp}
            self.events_received.append(event_with_timestamp)

            # Log event
            step = data.get('step', 'unknown')
            status = data.get('status', 'unknown')
            message = data.get('message', '')

            log_msg = f"📡 {step}:{status} - {message}"

            if data.get('agent_name'):
                log_msg += f" | Agent: {data['agent_name']}"
            if data.get('voice_model'):
                log_msg += f" | Voice: {data['voice_model']}"
            if data.get('error'):
                log_msg += f" | Error: {data['error']}"

            self.log(log_msg, "EVENT")

            # Check if completed
            if step == 'overall' and status in ['completed', 'failed']:
                self.test_completed = True
                if status == 'completed':
                    self.log("🎉 Agent creation completed successfully!", "SUCCESS")
                else:
                    self.log("❌ Agent creation failed!", "ERROR")

        @self.sio.event
        async def agent_creation_error(data):
            self.log(f"❌ Agent creation error: {json.dumps(data)}", "ERROR")

    async def test_websocket_communication(self):
        """Test complete WebSocket communication"""

        self.log("🧪 Starting WebSocket Communication Test", "HEADER")
        self.log("=" * 60, "HEADER")

        try:
            # Step 1: Connect to server
            self.log(f"🔌 Connecting to {self.server_url}...")
            await self.sio.connect(self.server_url)

            if not self.connected:
                self.log("❌ Failed to connect to WebSocket server", "ERROR")
                return False

            await asyncio.sleep(1)

            # Step 2: Send agent creation request
            self.log("📋 Preparing agent creation request...")

            test_requirements = {
                'business_name': 'WebSocket Test Pizza Co',
                'business_type': 'pizza restaurant',
                'target_audience': 'local community',
                'tone': 'friendly and enthusiastic',
                'main_functions': ['take_order', 'menu_inquiry', 'store_hours'],
                'voice_model': 'echo'  # Specifically request echo
            }

            session_id = f'websocket-test-{int(time.time())}'

            request_data = {
                'session_id': session_id,
                'requirements': test_requirements
            }

            self.log(f"🚀 Sending agent creation request...")
            self.log(f"   Session ID: {session_id}")
            self.log(f"   Business: {test_requirements['business_name']}")
            self.log(f"   Type: {test_requirements['business_type']}")
            self.log(f"   Voice: {test_requirements['voice_model']}")

            await self.sio.emit('start_agent_creation', request_data)

            # Step 3: Monitor for completion
            self.log("⏳ Monitoring agent creation progress...")

            timeout = 60  # 60 second timeout
            start_time = time.time()

            while time.time() - start_time < timeout:
                await asyncio.sleep(0.5)

                if self.test_completed:
                    break

            # Step 4: Analyze results
            self.log("📊 Analyzing results...")

            total_events = len(self.events_received)
            self.log(f"   Total events received: {total_events}")

            if total_events == 0:
                self.log("❌ No events received from server", "ERROR")
                return False

            # Check event sequence
            event_steps = [f"{e.get('step')}:{e.get('status')}" for e in self.events_received]
            self.log(f"   Event sequence: {' -> '.join(event_steps)}")

            # Check for voice model
            voice_events = [e for e in self.events_received if e.get('voice_model')]
            if voice_events:
                voice_used = voice_events[0]['voice_model']
                self.log(f"   Voice model used: {voice_used}")
            else:
                self.log("   No voice model information received")

            # Check for agent name
            agent_events = [e for e in self.events_received if e.get('agent_name')]
            if agent_events:
                agent_name = agent_events[0]['agent_name']
                self.log(f"   Agent name: {agent_name}")

            # Save detailed event log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            events_file = f"logs/websocket_events_{timestamp}.json"

            import os
            os.makedirs('logs', exist_ok=True)

            with open(events_file, 'w') as f:
                json.dump(self.events_received, f, indent=2)

            self.log(f"   Events saved to: {events_file}")

            # Success criteria
            success = (
                total_events > 0 and
                self.test_completed and
                any(e.get('status') == 'completed' for e in self.events_received)
            )

            return success

        except Exception as e:
            self.log(f"❌ WebSocket test failed: {e}", "ERROR")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False

        finally:
            if self.connected:
                await self.sio.disconnect()

async def main():
    print("🌐 WebSocket Client Test")
    print("=" * 50)
    print("This test connects to your webhook server and tests real WebSocket communication")
    print()
    print("Make sure your webhook server is running on localhost:5000")
    print("Run: python webhook_server.py")
    print()

    # Allow user to specify different URL
    server_url = 'http://localhost:5000'
    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    print(f"Testing WebSocket connection to: {server_url}")
    print()

    client = WebSocketClientTest(server_url)

    try:
        success = await client.test_websocket_communication()

        print()
        print("=" * 60)
        if success:
            print("✅ WebSocket communication test PASSED!")
            print("✅ Real-time events are working correctly")
            print("✅ Agent creation pipeline completed")
        else:
            print("❌ WebSocket communication test FAILED!")
            print("❌ Check the logs above for issues")

        print("=" * 60)
        return success

    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)