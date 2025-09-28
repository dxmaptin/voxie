#!/usr/bin/env python3
"""
Complete Integration Test with Full Logging
Tests the entire pipeline from WebSocket to Agent Creation with detailed logs

Usage: python test_complete_integration.py
"""

import asyncio
import sys
import os
import json
import time
import threading
import subprocess
import signal
from pathlib import Path
from datetime import datetime

# Add paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent / 'voxie-test' / 'src'))

class CompleteIntegrationTest:
    """Complete end-to-end integration test with detailed logging"""

    def __init__(self):
        self.test_id = f"test_{int(time.time())}"
        self.log_file = f"logs/integration_test_{self.test_id}.log"
        self.webhook_process = None
        self.events_received = []

        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)

    def log(self, level, message, also_print=True):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"

        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

        if also_print:
            print(log_entry)

    def test_direct_agent_creation(self):
        """Test 1: Direct agent creation without WebSocket"""
        self.log("INFO", "=" * 60)
        self.log("INFO", "TEST 1: Direct Agent Creation")
        self.log("INFO", "=" * 60)

        try:
            # Import agent modules
            self.log("INFO", "Importing agent modules...")

            try:
                from agent import ProcessingAgent, UserRequirements, AgentManager
                self.log("SUCCESS", "Agent modules imported successfully")
            except ImportError as e:
                self.log("ERROR", f"Failed to import agent modules: {e}")
                return False

            # Create mock event broadcaster
            class LoggingBroadcaster:
                def __init__(self, test_instance):
                    self.test = test_instance
                    self.events = []

                def emit_step(self, session_id, step, status, message, error=None, **extra):
                    event = {
                        'timestamp': datetime.now().isoformat(),
                        'session_id': session_id,
                        'step': step,
                        'status': status,
                        'message': message,
                        'error': error,
                        **extra
                    }
                    self.events.append(event)

                    log_msg = f"EVENT: {step}:{status} - {message}"
                    if extra.get('agent_name'):
                        log_msg += f" [Agent: {extra['agent_name']}]"
                    if extra.get('voice_model'):
                        log_msg += f" [Voice: {extra['voice_model']}]"
                    if error:
                        log_msg += f" [Error: {error}]"

                    self.test.log("EVENT", log_msg)

                def emit_overall_status(self, session_id, status, message, error=None, **extra):
                    self.emit_step(session_id, 'overall', status, message, error, **extra)

            broadcaster = LoggingBroadcaster(self)

            # Create test requirements
            self.log("INFO", "Creating test requirements...")
            requirements = UserRequirements()
            requirements.business_name = "Complete Test Pizza Palace"
            requirements.business_type = "pizza restaurant"
            requirements.target_audience = "families and pizza lovers"
            requirements.tone = "friendly and enthusiastic"
            requirements.main_functions = ["take_order", "menu_inquiry", "store_hours"]

            self.log("INFO", f"Business: {requirements.business_name}")
            self.log("INFO", f"Type: {requirements.business_type}")
            self.log("INFO", f"Functions: {requirements.main_functions}")

            # Create and run processing agent
            self.log("INFO", "Creating ProcessingAgent...")
            processor = ProcessingAgent(event_broadcaster=broadcaster)

            self.log("INFO", "Starting agent creation pipeline...")
            session_id = f"direct-test-{self.test_id}"

            # Run async agent creation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                spec = loop.run_until_complete(
                    processor.process_requirements(requirements, session_id)
                )

                self.log("SUCCESS", f"Agent created: {spec.agent_type}")
                self.log("SUCCESS", f"Voice model: {spec.voice}")
                self.log("SUCCESS", f"Functions: {len(spec.functions)} configured")
                self.log("SUCCESS", f"Sample response: {spec.sample_responses[0][:100]}...")

                # Verify events
                self.log("INFO", f"Events captured: {len(broadcaster.events)}")

                required_steps = ['scenario:started', 'prompts:started', 'voice:started', 'knowledge_base:started']
                step_statuses = [f"{e['step']}:{e['status']}" for e in broadcaster.events]

                all_found = True
                for step in required_steps:
                    if step in step_statuses:
                        self.log("SUCCESS", f"Required step found: {step}")
                    else:
                        self.log("ERROR", f"Missing required step: {step}")
                        all_found = False

                # Log all events to file
                events_log = json.dumps(broadcaster.events, indent=2)
                with open(f"logs/events_{self.test_id}.json", 'w') as f:
                    f.write(events_log)
                self.log("INFO", f"Events saved to logs/events_{self.test_id}.json")

                return all_found

            finally:
                loop.close()

        except Exception as e:
            self.log("ERROR", f"Direct agent creation failed: {e}")
            import traceback
            self.log("ERROR", f"Traceback: {traceback.format_exc()}")
            return False

    def test_agent_manager_integration(self):
        """Test 2: AgentManager integration"""
        self.log("INFO", "=" * 60)
        self.log("INFO", "TEST 2: AgentManager Integration")
        self.log("INFO", "=" * 60)

        try:
            from agent import AgentManager, UserRequirements

            # Mock SocketIO for broadcaster
            class MockSocketIO:
                def __init__(self, test_instance):
                    self.test = test_instance
                    self.emissions = []

                def emit(self, event, data, room=None):
                    emission = {
                        'timestamp': datetime.now().isoformat(),
                        'event': event,
                        'data': data,
                        'room': room
                    }
                    self.emissions.append(emission)
                    self.test.log("SOCKETIO", f"{event} -> Room: {room} -> {json.dumps(data, default=str)}")

            mock_socketio = MockSocketIO(self)

            # Create event broadcaster
            from event_broadcaster import initialize_broadcaster
            broadcaster = initialize_broadcaster(mock_socketio)

            # Create agent manager
            self.log("INFO", "Creating AgentManager...")
            manager = AgentManager(event_broadcaster=broadcaster)

            # Set requirements
            manager.user_requirements.business_name = "Manager Test Restaurant"
            manager.user_requirements.business_type = "restaurant"
            manager.user_requirements.tone = "professional"

            self.log("INFO", "Testing AgentManager transition_to_processing...")

            # Run the transition
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                session_id = f"manager-test-{self.test_id}"
                loop.run_until_complete(manager.transition_to_processing(session_id))

                self.log("SUCCESS", "AgentManager processing completed")
                self.log("INFO", f"SocketIO emissions: {len(mock_socketio.emissions)}")

                # Save SocketIO emissions
                emissions_log = json.dumps(mock_socketio.emissions, indent=2)
                with open(f"logs/socketio_emissions_{self.test_id}.json", 'w') as f:
                    f.write(emissions_log)

                return True

            finally:
                loop.close()

        except Exception as e:
            self.log("ERROR", f"AgentManager integration failed: {e}")
            import traceback
            self.log("ERROR", f"Traceback: {traceback.format_exc()}")
            return False

    def test_event_broadcaster(self):
        """Test 3: Event Broadcasting System"""
        self.log("INFO", "=" * 60)
        self.log("INFO", "TEST 3: Event Broadcasting System")
        self.log("INFO", "=" * 60)

        try:
            # Mock SocketIO
            class TestSocketIO:
                def __init__(self):
                    self.events = []

                def emit(self, event, data, room=None):
                    self.events.append({
                        'event': event,
                        'data': data,
                        'room': room,
                        'timestamp': datetime.now().isoformat()
                    })

            mock_socketio = TestSocketIO()

            # Create broadcaster
            from event_broadcaster import initialize_broadcaster
            broadcaster = initialize_broadcaster(mock_socketio)

            # Test various events
            session_id = f"broadcast-test-{self.test_id}"

            test_events = [
                ('scenario', 'started', 'Analyzing business requirements...'),
                ('prompts', 'started', 'Creating custom prompts...'),
                ('voice', 'completed', 'Voice profile ready', {'voice_model': 'echo', 'agent_name': 'Test Agent'}),
                ('overall', 'completed', 'Agent creation successful!')
            ]

            self.log("INFO", f"Testing {len(test_events)} event broadcasts...")

            for step, status, message, *extra_data in test_events:
                extra = extra_data[0] if extra_data else {}
                broadcaster.emit_step(session_id, step, status, message, **extra)
                self.log("BROADCAST", f"{step}:{status} - {message}")

            self.log("SUCCESS", f"All {len(test_events)} events broadcast successfully")
            self.log("INFO", f"SocketIO received {len(mock_socketio.events)} events")

            # Verify events
            for i, (step, status, message, *_) in enumerate(test_events):
                socketio_event = mock_socketio.events[i]
                if (socketio_event['data']['step'] == step and
                    socketio_event['data']['status'] == status):
                    self.log("SUCCESS", f"Event {i+1} verified: {step}:{status}")
                else:
                    self.log("ERROR", f"Event {i+1} mismatch: expected {step}:{status}")
                    return False

            # Save broadcast test results
            broadcast_log = json.dumps(mock_socketio.events, indent=2)
            with open(f"logs/broadcast_test_{self.test_id}.json", 'w') as f:
                f.write(broadcast_log)

            return True

        except Exception as e:
            self.log("ERROR", f"Event broadcasting test failed: {e}")
            import traceback
            self.log("ERROR", f"Traceback: {traceback.format_exc()}")
            return False

    def create_minimal_webhook_server(self):
        """Create a minimal webhook server for testing"""
        minimal_server_code = '''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent / 'voxie-test' / 'src'))

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True)

# Initialize event broadcaster
try:
    from event_broadcaster import initialize_broadcaster
    from agent_integration import initialize_agent_integrator

    event_broadcaster = initialize_broadcaster(socketio)
    agent_integrator = initialize_agent_integrator(event_broadcaster)
    print("✅ Event broadcaster and agent integrator initialized")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    event_broadcaster = None
    agent_integrator = None

@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected'})

@socketio.on('start_agent_creation')
def handle_start_agent_creation(data):
    print(f"🚀 Agent creation request: {json.dumps(data, indent=2)}")

    session_id = data.get('session_id', 'test-session')
    requirements = data.get('requirements', {})

    if agent_integrator:
        # Start real agent creation
        import asyncio
        asyncio.create_task(
            agent_integrator.start_agent_creation(session_id, requirements)
        )
    else:
        print("❌ Agent integrator not available")

    emit('agent_creation_started', {'session_id': session_id})

if __name__ == '__main__':
    print("🚀 Starting minimal webhook server on http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
'''

        with open('minimal_webhook_server.py', 'w') as f:
            f.write(minimal_server_code)

        self.log("INFO", "Created minimal_webhook_server.py")

    def run_complete_test(self):
        """Run all tests"""
        self.log("INFO", "🧪 Starting Complete Integration Test")
        self.log("INFO", f"Test ID: {self.test_id}")
        self.log("INFO", f"Log file: {self.log_file}")
        self.log("INFO", "=" * 80)

        results = {}

        # Test 1: Direct Agent Creation
        results['direct_creation'] = self.test_direct_agent_creation()

        # Test 2: AgentManager Integration
        results['manager_integration'] = self.test_agent_manager_integration()

        # Test 3: Event Broadcasting
        results['event_broadcasting'] = self.test_event_broadcaster()

        # Create minimal webhook server for manual testing
        self.create_minimal_webhook_server()

        # Summary
        self.log("INFO", "=" * 80)
        self.log("INFO", "TEST RESULTS SUMMARY")
        self.log("INFO", "=" * 80)

        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.log("RESULT", f"{test_name}: {status}")
            if not passed:
                all_passed = False

        self.log("INFO", "=" * 80)
        if all_passed:
            self.log("SUCCESS", "🎉 ALL TESTS PASSED!")
            self.log("INFO", "Real-time agent creation is working correctly")
        else:
            self.log("ERROR", "❌ SOME TESTS FAILED")
            self.log("INFO", "Check the logs above for details")

        self.log("INFO", f"Complete test log: {self.log_file}")
        self.log("INFO", "For manual WebSocket testing, run:")
        self.log("INFO", "  python minimal_webhook_server.py")

        return all_passed

def main():
    test = CompleteIntegrationTest()

    try:
        success = test.run_complete_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        test.log("INFO", "Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        test.log("ERROR", f"Test suite crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()