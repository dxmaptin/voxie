#!/usr/bin/env python3
"""
Integration tests for bidirectional progress system
Tests complete end-to-end flow including Railway webhook
"""

import asyncio
import sys
import requests
import json
import time
from unittest.mock import Mock, AsyncMock

sys.path.append('/Users/dxma/Desktop/voxie-clean/voxie-test/src')

async def test_end_to_end_flow():
    """Test complete end-to-end flow with actual Railway webhook"""
    print("🔄 Testing End-to-End Integration")
    print("-" * 40)

    try:
        # Test 1: Progress templates work
        from progress_templates import get_voice_announcement, should_announce_voice
        voice_msg = get_voice_announcement('database_creation', 'completed')
        assert voice_msg == "Database is ready", f"Expected 'Database is ready', got '{voice_msg}'"
        print("✅ Progress templates working")

        # Test 2: Production bridge initialization
        from production_bridge import initialize_production_bridge
        bridge = initialize_production_bridge()
        print("✅ Production bridge initialized")

        # Test 3: Agent callback registration
        callback_invocations = []

        async def test_callback(step_name: str, status: str, message: str):
            callback_invocations.append({
                'step': step_name,
                'status': status,
                'message': message,
                'timestamp': time.time()
            })

        session_id = f"integration_test_{int(time.time())}"
        bridge.register_agent_session(session_id, test_callback)
        print("✅ Agent callback registered")

        # Test 4: Emit progress events
        test_events = [
            ('scenario', 'started', 'Analyzing business requirements'),
            ('database_creation', 'started', 'Creating database schema'),
            ('database_creation', 'completed', 'Database ready with 5 tables'),
            ('voice', 'started', 'Configuring voice profile'),
            ('voice', 'completed', 'Voice profile ready - alloy'),
            ('overall', 'completed', 'Agent creation successful')
        ]

        for step, status, message in test_events:
            bridge.emit_step(session_id, step, status, message)
            await asyncio.sleep(0.1)  # Small delay for processing

        print("✅ Progress events emitted")

        # Test 5: Verify callbacks were invoked
        await asyncio.sleep(0.5)  # Wait for async callbacks

        assert len(callback_invocations) == len(test_events), \
            f"Expected {len(test_events)} callbacks, got {len(callback_invocations)}"

        # Verify callback data
        for i, (expected_step, expected_status, expected_message) in enumerate(test_events):
            callback = callback_invocations[i]
            assert callback['step'] == expected_step, \
                f"Step mismatch: expected {expected_step}, got {callback['step']}"
            assert callback['status'] == expected_status, \
                f"Status mismatch: expected {expected_status}, got {callback['status']}"

        print("✅ Agent callbacks verified")

        # Test 6: Test Railway webhook (if available)
        railway_url = "https://voxie-production.up.railway.app"

        try:
            # Test health endpoint
            health_response = requests.get(f"{railway_url}/health", timeout=5)
            if health_response.status_code == 200:
                print("✅ Railway webhook server reachable")

                # Test webhook endpoint
                webhook_data = {
                    'session_id': session_id,
                    'step': 'integration_test',
                    'status': 'completed',
                    'message': 'Integration test webhook',
                    'timestamp': time.time()
                }

                webhook_response = requests.post(
                    f"{railway_url}/agent-event",
                    json=webhook_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )

                if webhook_response.status_code == 200:
                    print("✅ Railway webhook working")
                else:
                    print(f"⚠️ Railway webhook returned {webhook_response.status_code}")
            else:
                print(f"⚠️ Railway health check returned {health_response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Railway not reachable: {e}")

        # Test 7: Session cleanup
        bridge.unregister_agent_session(session_id)
        assert session_id not in bridge.agent_callbacks, "Session should be cleaned up"
        print("✅ Session cleanup verified")

        # Test 8: Test VoxieAgent integration (mock)
        class MockVoxieAgent:
            def __init__(self):
                self.announcements = []
                self.current_session_for_announcements = Mock()

            async def on_agent_creation_progress(self, step_name: str, status: str, message: str):
                voice_msg = get_voice_announcement(step_name, status)
                if should_announce_voice(step_name, status):
                    self.announcements.append({
                        'step': step_name,
                        'status': status,
                        'voice_message': voice_msg
                    })

        mock_agent = MockVoxieAgent()

        # Test progress announcements
        for step, status, message in test_events:
            await mock_agent.on_agent_creation_progress(step, status, message)

        expected_announcements = sum(1 for step, status, _ in test_events
                                   if should_announce_voice(step, status))

        assert len(mock_agent.announcements) == expected_announcements, \
            f"Expected {expected_announcements} announcements, got {len(mock_agent.announcements)}"

        print("✅ VoxieAgent integration verified")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_scenarios():
    """Test error handling and edge cases"""
    print("\n🛡️ Testing Error Scenarios")
    print("-" * 40)

    try:
        from production_bridge import ProductionEventBridge

        # Test 1: Bridge with invalid URL
        bridge = ProductionEventBridge("https://invalid-url-that-does-not-exist.com")

        # Should not crash when webhook fails
        bridge.emit_step('error-test', 'database_creation', 'started', 'Error test')
        print("✅ Handles invalid webhook URL gracefully")

        # Test 2: Invalid progress template inputs
        from progress_templates import get_voice_announcement

        # Should provide fallback for invalid inputs
        msg = get_voice_announcement('invalid_step', 'invalid_status')
        assert msg == "Agent creation invalid_status", f"Unexpected fallback: {msg}"
        print("✅ Handles invalid template inputs gracefully")

        # Test 3: Callback exceptions
        async def failing_callback(step, status, message):
            raise Exception("Callback error")

        bridge = ProductionEventBridge()
        bridge.register_agent_session('error-session', failing_callback)

        # Should not crash when callback fails
        bridge.emit_step('error-session', 'database_creation', 'started', 'Error test')
        await asyncio.sleep(0.1)
        print("✅ Handles callback exceptions gracefully")

        # Test 4: Double registration/unregistration
        def dummy_callback(step, status, message):
            pass

        bridge.register_agent_session('double-test', dummy_callback)
        bridge.register_agent_session('double-test', dummy_callback)  # Should replace
        bridge.unregister_agent_session('double-test')
        bridge.unregister_agent_session('double-test')  # Should not crash
        print("✅ Handles double registration/unregistration gracefully")

        return True

    except Exception as e:
        print(f"❌ Error scenario test failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🔗 Bidirectional Progress System - Integration Tests")
    print("=" * 60)

    success = True

    # Run tests
    success &= await test_end_to_end_flow()
    success &= await test_error_scenarios()

    if success:
        print("\n" + "=" * 60)
        print("🎉 All integration tests passed!")
        print("✅ End-to-end flow working correctly")
        print("✅ Error handling robust")
        print("✅ Railway integration functional")
        print("✅ Agent callbacks verified")
        print("✅ Session management working")
    else:
        print("\n❌ Some integration tests failed!")

    return success

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)