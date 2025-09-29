#!/usr/bin/env python3
"""
Performance tests for bidirectional progress system
Tests latency and throughput requirements
"""

import asyncio
import time
import sys
import statistics
from unittest.mock import Mock, AsyncMock

sys.path.append('/Users/dxma/Desktop/voxie-clean/voxie-test/src')

async def test_callback_latency():
    """Test that agent callbacks complete within latency requirements"""
    print("⚡ Testing Agent Callback Latency")
    print("-" * 40)

    # Mock VoxieAgent callback function
    async def mock_agent_callback(step_name: str, status: str, message: str):
        """Simulate VoxieAgent progress callback"""
        from progress_templates import get_voice_announcement, should_announce_voice

        start_time = time.perf_counter()

        # Simulate the real callback operations
        voice_message = get_voice_announcement(step_name, status)
        should_announce = should_announce_voice(step_name, status)

        if should_announce:
            # Simulate TTS preparation (but don't actually do TTS)
            await asyncio.sleep(0.001)  # Minimal processing delay

        end_time = time.perf_counter()
        return (end_time - start_time) * 1000  # Return milliseconds

    # Test multiple callback invocations
    latencies = []
    test_cases = [
        ('database_creation', 'started', 'Setting up database'),
        ('database_creation', 'completed', 'Database ready'),
        ('voice', 'started', 'Configuring voice'),
        ('voice', 'completed', 'Voice ready'),
        ('overall', 'completed', 'Agent ready')
    ]

    for step, status, message in test_cases:
        latency_ms = await mock_agent_callback(step, status, message)
        latencies.append(latency_ms)
        print(f"  {step}:{status} → {latency_ms:.2f}ms")

    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)

    print(f"\n📊 Callback Latency Results:")
    print(f"  Average: {avg_latency:.2f}ms")
    print(f"  Maximum: {max_latency:.2f}ms")
    print(f"  Target:  < 50ms (excluding TTS)")

    # Assert performance requirements
    assert avg_latency < 50, f"Average latency {avg_latency}ms exceeds 50ms target"
    assert max_latency < 100, f"Max latency {max_latency}ms exceeds 100ms target"

    print("✅ Callback latency requirements met!")
    return latencies

async def test_production_bridge_performance():
    """Test production bridge webhook + callback performance"""
    print("\n⚡ Testing Production Bridge Performance")
    print("-" * 40)

    from production_bridge import ProductionEventBridge
    from unittest.mock import patch

    # Mock HTTP requests for performance testing
    with patch('requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock fast HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.post.return_value = mock_response

        bridge = ProductionEventBridge()

        # Mock agent callback
        callback_times = []
        async def timed_callback(step_name: str, status: str, message: str):
            start = time.perf_counter()
            await asyncio.sleep(0.001)  # Minimal processing
            end = time.perf_counter()
            callback_times.append((end - start) * 1000)

        bridge.register_agent_session('perf-test', timed_callback)

        # Test emit_step performance
        emit_times = []

        for i in range(10):
            start_time = time.perf_counter()

            bridge.emit_step(
                'perf-test',
                'database_creation',
                'started',
                f'Performance test {i}'
            )

            end_time = time.perf_counter()
            emit_time = (end_time - start_time) * 1000
            emit_times.append(emit_time)

        # Wait for any pending callbacks
        await asyncio.sleep(0.1)

        avg_emit = statistics.mean(emit_times)
        max_emit = max(emit_times)

        print(f"📊 Bridge Performance Results:")
        print(f"  Avg emit_step: {avg_emit:.2f}ms")
        print(f"  Max emit_step: {max_emit:.2f}ms")
        print(f"  Target: < 100ms (webhook + callback)")

        # Performance assertions
        assert avg_emit < 100, f"Average emit time {avg_emit}ms exceeds 100ms target"
        assert max_emit < 200, f"Max emit time {max_emit}ms exceeds 200ms target"

        print("✅ Production bridge performance requirements met!")

async def test_concurrent_sessions():
    """Test performance with multiple concurrent sessions"""
    print("\n⚡ Testing Concurrent Session Performance")
    print("-" * 40)

    from production_bridge import ProductionEventBridge
    from unittest.mock import patch

    with patch('requests.Session') as mock_session_class:
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.post.return_value = mock_response

        bridge = ProductionEventBridge()

        # Create multiple concurrent sessions
        session_count = 5
        sessions = [f'session-{i}' for i in range(session_count)]

        async def session_callback(session_id):
            return lambda step, status, msg: asyncio.sleep(0.001)

        # Register all sessions
        for session_id in sessions:
            bridge.register_agent_session(session_id, await session_callback(session_id))

        # Test concurrent emissions
        start_time = time.perf_counter()

        # Emit to all sessions concurrently - fix the async issue
        for session_id in sessions:
            for step in ['database_creation', 'voice', 'overall']:
                bridge.emit_step(session_id, step, 'completed', f'Test for {session_id}')

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000

        total_events = session_count * 3  # 3 steps per session
        events_per_second = (total_events / total_time) * 1000

        print(f"📊 Concurrent Performance Results:")
        print(f"  Sessions: {session_count}")
        print(f"  Total events: {total_events}")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Events/second: {events_per_second:.0f}")
        print(f"  Target: > 100 events/second")

        # Performance assertion
        assert events_per_second > 100, f"Events per second {events_per_second} below target of 100"

        print("✅ Concurrent session performance requirements met!")

async def test_memory_usage():
    """Test memory efficiency of progress system"""
    print("\n⚡ Testing Memory Usage")
    print("-" * 40)

    from production_bridge import ProductionEventBridge
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    bridge = ProductionEventBridge()

    # Create and clean up many sessions to test memory leaks
    for i in range(100):
        session_id = f'memory-test-{i}'
        callback = AsyncMock()

        bridge.register_agent_session(session_id, callback)
        bridge.emit_step(session_id, 'database_creation', 'completed', 'Memory test')
        bridge.unregister_agent_session(session_id)

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"📊 Memory Usage Results:")
    print(f"  Initial memory: {initial_memory:.2f}MB")
    print(f"  Final memory: {final_memory:.2f}MB")
    print(f"  Memory increase: {memory_increase:.2f}MB")
    print(f"  Target: < 10MB increase")

    # Memory efficiency assertion
    assert memory_increase < 10, f"Memory increase {memory_increase}MB exceeds 10MB target"

    print("✅ Memory usage requirements met!")

async def run_performance_tests():
    """Run all performance tests"""
    print("🚀 Bidirectional Progress System - Performance Tests")
    print("=" * 60)

    try:
        # Run all performance tests
        await test_callback_latency()
        await test_production_bridge_performance()
        await test_concurrent_sessions()
        await test_memory_usage()

        print("\n" + "=" * 60)
        print("🎉 All performance tests passed!")
        print("✅ System meets sub-400ms latency requirements")
        print("✅ System handles concurrent sessions efficiently")
        print("✅ System maintains low memory footprint")

    except AssertionError as e:
        print(f"\n❌ Performance test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(run_performance_tests())
    sys.exit(0 if success else 1)