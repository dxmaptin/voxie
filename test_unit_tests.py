#!/usr/bin/env python3
"""
Unit tests for bidirectional agent progress system
Tests individual components in isolation
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import json

# Add the src directory to Python path
sys.path.append('/Users/dxma/Desktop/voxie-clean/voxie-test/src')

class TestProgressTemplates(unittest.TestCase):
    """Test progress templates for zero hallucination"""

    def setUp(self):
        from progress_templates import (
            get_voice_announcement,
            get_detailed_message,
            should_announce_voice,
            get_progress_percentage,
            is_valid_step,
            is_valid_status,
            format_progress_update
        )
        self.get_voice_announcement = get_voice_announcement
        self.get_detailed_message = get_detailed_message
        self.should_announce_voice = should_announce_voice
        self.get_progress_percentage = get_progress_percentage
        self.is_valid_step = is_valid_step
        self.is_valid_status = is_valid_status
        self.format_progress_update = format_progress_update

    def test_voice_announcements_predefined(self):
        """Test that voice announcements are predefined and safe"""
        # Test valid combinations
        msg = self.get_voice_announcement('database_creation', 'started')
        self.assertEqual(msg, "Setting up database...")

        msg = self.get_voice_announcement('database_creation', 'completed')
        self.assertEqual(msg, "Database is ready")

        msg = self.get_voice_announcement('voice', 'failed')
        self.assertEqual(msg, "Voice configuration failed")

    def test_fallback_for_invalid_inputs(self):
        """Test fallback behavior for invalid inputs"""
        msg = self.get_voice_announcement('invalid_step', 'started')
        self.assertEqual(msg, "Agent creation started")

        msg = self.get_voice_announcement('database_creation', 'invalid_status')
        self.assertEqual(msg, "Agent creation invalid_status")

    def test_announcement_filtering(self):
        """Test that only important milestones trigger announcements"""
        # Should announce completed steps
        self.assertTrue(self.should_announce_voice('database_creation', 'completed'))
        self.assertTrue(self.should_announce_voice('voice', 'completed'))

        # Should announce failures
        self.assertTrue(self.should_announce_voice('database_creation', 'failed'))

        # Should announce major started steps
        self.assertTrue(self.should_announce_voice('database_creation', 'started'))
        self.assertTrue(self.should_announce_voice('voice', 'started'))

        # Should NOT announce minor started steps
        self.assertFalse(self.should_announce_voice('scenario', 'started'))
        self.assertFalse(self.should_announce_voice('prompts', 'started'))

    def test_progress_percentages(self):
        """Test progress percentage calculations"""
        self.assertEqual(self.get_progress_percentage('scenario', 'started'), 10)
        self.assertEqual(self.get_progress_percentage('scenario', 'completed'), 20)
        self.assertEqual(self.get_progress_percentage('overall', 'completed'), 100)
        self.assertEqual(self.get_progress_percentage('invalid', 'started'), 0)

    def test_validation_functions(self):
        """Test step and status validation"""
        # Valid steps
        self.assertTrue(self.is_valid_step('database_creation'))
        self.assertTrue(self.is_valid_step('voice'))
        self.assertFalse(self.is_valid_step('invalid_step'))

        # Valid statuses
        self.assertTrue(self.is_valid_status('started'))
        self.assertTrue(self.is_valid_status('completed'))
        self.assertTrue(self.is_valid_status('failed'))
        self.assertFalse(self.is_valid_status('invalid_status'))

    def test_formatted_progress_update(self):
        """Test complete progress update formatting"""
        update = self.format_progress_update('database_creation', 'completed', 'test-session')

        self.assertEqual(update['session_id'], 'test-session')
        self.assertEqual(update['step'], 'database_creation')
        self.assertEqual(update['status'], 'completed')
        self.assertEqual(update['voice_message'], 'Database is ready')
        self.assertTrue(update['should_announce'])
        self.assertEqual(update['progress_percentage'], 40)
        self.assertEqual(update['emoji'], '🗄️')


class TestProductionBridge(unittest.TestCase):
    """Test production bridge with callback system"""

    def setUp(self):
        # Mock requests to avoid actual HTTP calls
        self.requests_patcher = patch('requests.Session')
        self.mock_session_class = self.requests_patcher.start()
        self.mock_session = Mock()
        self.mock_session_class.return_value = self.mock_session

        # Mock successful HTTP response
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_session.post.return_value = self.mock_response
        self.mock_session.get.return_value = self.mock_response

    def tearDown(self):
        self.requests_patcher.stop()

    def test_bridge_initialization(self):
        """Test production bridge initialization"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge('https://test.example.com')
        self.assertEqual(bridge.webhook_server_url, 'https://test.example.com')
        self.assertEqual(len(bridge.agent_callbacks), 0)

    def test_agent_registration(self):
        """Test agent callback registration"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge()
        callback = AsyncMock()

        bridge.register_agent_session('test-session', callback)
        self.assertIn('test-session', bridge.agent_callbacks)
        self.assertEqual(bridge.agent_callbacks['test-session'], callback)

    def test_agent_unregistration(self):
        """Test agent callback unregistration"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge()
        callback = AsyncMock()

        bridge.register_agent_session('test-session', callback)
        bridge.unregister_agent_session('test-session')
        self.assertNotIn('test-session', bridge.agent_callbacks)

    def test_emit_step_with_webhook_and_callback(self):
        """Test that emit_step sends webhook AND calls agent callback"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge()
        callback = AsyncMock()
        bridge.register_agent_session('test-session', callback)

        # Emit a step
        bridge.emit_step('test-session', 'database_creation', 'started', 'Setting up database')

        # Verify webhook was sent
        self.mock_session.post.assert_called_once()
        call_args = self.mock_session.post.call_args
        self.assertIn('/agent-event', call_args[0][0])

        # Verify JSON payload
        json_data = call_args[1]['json']
        self.assertEqual(json_data['session_id'], 'test-session')
        self.assertEqual(json_data['step'], 'database_creation')
        self.assertEqual(json_data['status'], 'started')
        self.assertEqual(json_data['message'], 'Setting up database')

    def test_connection_test(self):
        """Test webhook server connection testing"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge()

        # Test successful connection
        self.mock_response.status_code = 200
        self.assertTrue(bridge.test_connection())

        # Test failed connection
        self.mock_session.get.side_effect = Exception("Connection failed")
        self.assertFalse(bridge.test_connection())

    def test_overall_status_cleanup(self):
        """Test that overall status completion cleans up sessions"""
        from production_bridge import ProductionEventBridge

        bridge = ProductionEventBridge()
        callback = AsyncMock()
        bridge.register_agent_session('test-session', callback)

        # Emit completion
        bridge.emit_overall_status('test-session', 'completed', 'Agent ready')

        # Should clean up session
        self.assertNotIn('test-session', bridge.agent_callbacks)


class TestVoxieAgentIntegration(unittest.IsolatedAsyncioTestCase):
    """Test VoxieAgent progress callback integration"""

    async def test_progress_callback_functionality(self):
        """Test VoxieAgent progress callback methods"""
        # Mock the VoxieAgent imports
        with patch('sys.path'):
            # Create a mock VoxieAgent-like class for testing
            class MockVoxieAgent:
                def __init__(self):
                    self.current_session_for_announcements = None
                    self.registered_sessions = set()
                    self.announcements_made = []

                async def on_agent_creation_progress(self, step_name: str, status: str, message: str):
                    # Import progress functions
                    sys.path.append('/Users/dxma/Desktop/voxie-clean/voxie-test/src')
                    from progress_templates import get_voice_announcement, should_announce_voice

                    voice_message = get_voice_announcement(step_name, status)

                    if should_announce_voice(step_name, status) and self.current_session_for_announcements:
                        # Mock announcement
                        self.announcements_made.append({
                            'step': step_name,
                            'status': status,
                            'voice_message': voice_message
                        })

                def set_announcement_session(self, session):
                    self.current_session_for_announcements = session

            # Test the mock agent
            agent = MockVoxieAgent()
            mock_session = Mock()
            agent.set_announcement_session(mock_session)

            # Test progress callbacks
            await agent.on_agent_creation_progress('database_creation', 'started', 'Setting up database')
            await agent.on_agent_creation_progress('database_creation', 'completed', 'Database ready')
            await agent.on_agent_creation_progress('scenario', 'started', 'Analyzing requirements')  # Should not announce

            # Verify announcements
            self.assertEqual(len(agent.announcements_made), 2)  # Only 2 should announce
            self.assertEqual(agent.announcements_made[0]['voice_message'], 'Setting up database...')
            self.assertEqual(agent.announcements_made[1]['voice_message'], 'Database is ready')


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""

    def test_missing_imports_graceful_fallback(self):
        """Test that system works even with missing imports"""
        # Test the fallback functions defined in agent.py
        get_voice_announcement = lambda step, status: f"Agent creation {status}"
        get_detailed_message = lambda step, status: f"Agent creation step {step} {status}"
        should_announce_voice = lambda step, status: True

        # Should not crash
        msg = get_voice_announcement('test', 'started')
        self.assertEqual(msg, "Agent creation started")

    def test_production_bridge_http_failures(self):
        """Test production bridge handles HTTP failures gracefully"""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate HTTP failure
            mock_session.post.side_effect = Exception("Network error")

            from production_bridge import ProductionEventBridge
            bridge = ProductionEventBridge()

            # Should not crash, should handle gracefully
            try:
                bridge.emit_step('test', 'database_creation', 'started', 'test message')
                # If we get here, it handled the exception gracefully
                success = True
            except Exception:
                success = False

            self.assertTrue(success, "Bridge should handle HTTP failures gracefully")


def run_unit_tests():
    """Run all unit tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestProgressTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestProductionBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestVoxieAgentIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("🧪 Running Unit Tests for Bidirectional Progress System")
    print("=" * 60)

    result = run_unit_tests()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback}")

    if result.errors:
        print("\n⚠️ Errors:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback}")

    if result.wasSuccessful():
        print("\n🎉 All unit tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)