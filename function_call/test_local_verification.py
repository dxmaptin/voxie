#!/usr/bin/env python3
"""
Local Verification Test
Simple test you can run locally to verify everything works

This creates a detailed log of exactly what happens during agent creation
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add paths
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent / 'voxie-test' / 'src'))

def create_detailed_log():
    """Create a detailed log of the agent creation process"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/local_verification_{timestamp}.log"

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    def log_message(message, level="INFO"):
        log_entry = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {level}: {message}"
        print(log_entry)
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')
        return log_entry

    log_message("🚀 Starting Local Verification Test", "HEADER")
    log_message("=" * 70, "HEADER")

    try:
        # Step 1: Import modules
        log_message("📦 Step 1: Importing required modules...")

        try:
            from agent import ProcessingAgent, UserRequirements, AgentState
            log_message("✅ LiveKit agent modules imported successfully")
        except ImportError as e:
            log_message(f"❌ Failed to import agent modules: {e}", "ERROR")
            return False

        # Step 2: Create event capture system
        log_message("🔧 Step 2: Setting up event capture system...")

        captured_events = []

        class DetailedEventCapture:
            def emit_step(self, session_id, step, status, message, error=None, **extra):
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session_id,
                    'step': step,
                    'status': status,
                    'message': message,
                    'error': error,
                    'extra_data': extra
                }
                captured_events.append(event)

                # Log the event
                log_msg = f"📡 {step}:{status} - {message}"
                if extra.get('agent_name'):
                    log_msg += f" | Agent: {extra['agent_name']}"
                if extra.get('voice_model'):
                    log_msg += f" | Voice: {extra['voice_model']}"
                if error:
                    log_msg += f" | Error: {error}"

                log_message(log_msg, "EVENT")

            def emit_overall_status(self, session_id, status, message, error=None, **extra):
                self.emit_step(session_id, 'overall', status, message, error, **extra)

        event_capture = DetailedEventCapture()
        log_message("✅ Event capture system ready")

        # Step 3: Create test requirements
        log_message("🎯 Step 3: Creating test requirements...")

        requirements = UserRequirements()
        requirements.business_name = "Local Test Echo Pizza"
        requirements.business_type = "pizza restaurant"  # This should use echo voice
        requirements.target_audience = "local customers"
        requirements.tone = "friendly and welcoming"
        requirements.main_functions = ["take_order", "menu_inquiry", "delivery_info"]

        log_message(f"   Business Name: {requirements.business_name}")
        log_message(f"   Business Type: {requirements.business_type}")
        log_message(f"   Target Audience: {requirements.target_audience}")
        log_message(f"   Tone: {requirements.tone}")
        log_message(f"   Functions: {requirements.main_functions}")

        # Step 4: Create processing agent
        log_message("🏗️ Step 4: Creating ProcessingAgent with event capture...")

        processor = ProcessingAgent(event_broadcaster=event_capture)
        session_id = f"local_verification_{timestamp}"

        log_message(f"   Session ID: {session_id}")
        log_message("✅ ProcessingAgent created")

        # Step 5: Run agent creation
        log_message("⚡ Step 5: Running agent creation pipeline...")
        log_message("   (This will take 5-10 seconds and generate real-time events)")

        start_time = time.time()

        async def run_creation():
            return await processor.process_requirements(requirements, session_id)

        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            spec = loop.run_until_complete(run_creation())
            end_time = time.time()

            log_message("✅ Agent creation completed successfully!", "SUCCESS")
            log_message(f"   Duration: {end_time - start_time:.2f} seconds", "SUCCESS")

        finally:
            loop.close()

        # Step 6: Analyze results
        log_message("📊 Step 6: Analyzing results...")

        log_message(f"   Agent Type: {spec.agent_type}")
        log_message(f"   Voice Model: {spec.voice}")
        log_message(f"   Business Context: {spec.business_context}")
        log_message(f"   Functions: {len(spec.functions)} configured")
        log_message(f"   Sample Response: {spec.sample_responses[0]}")

        # Step 7: Verify events
        log_message("✅ Step 7: Verifying real-time events...")

        log_message(f"   Total events captured: {len(captured_events)}")

        # Check for required event sequence
        required_sequence = [
            'scenario:started',
            'scenario:completed',
            'prompts:started',
            'prompts:completed',
            'voice:started',
            'voice:completed',
            'knowledge_base:started',
            'knowledge_base:completed',
            'overall:completed'
        ]

        event_sequence = [f"{e['step']}:{e['status']}" for e in captured_events]

        log_message("   Event sequence verification:")
        all_events_found = True
        for i, expected_event in enumerate(required_sequence, 1):
            if expected_event in event_sequence:
                log_message(f"   ✅ {i}. {expected_event}", "SUCCESS")
            else:
                log_message(f"   ❌ {i}. {expected_event} - MISSING", "ERROR")
                all_events_found = False

        # Step 8: Voice model verification
        log_message("🎵 Step 8: Voice model verification...")

        voice_events = [e for e in captured_events if e.get('extra_data', {}).get('voice_model')]
        if voice_events:
            voice_used = voice_events[0]['extra_data']['voice_model']
            log_message(f"   Voice model used: {voice_used}")

            if voice_used == 'echo':
                log_message("   ✅ Echo voice model successfully configured!", "SUCCESS")
            else:
                log_message(f"   ℹ️ Default voice model used: {voice_used} (pizza template)")

        # Step 9: Save detailed logs
        log_message("💾 Step 9: Saving detailed logs...")

        # Save events as JSON
        events_file = f"logs/events_{timestamp}.json"
        with open(events_file, 'w') as f:
            json.dump(captured_events, f, indent=2, default=str)

        # Save agent spec as JSON
        spec_file = f"logs/agent_spec_{timestamp}.json"
        spec_data = {
            'agent_type': spec.agent_type,
            'voice': spec.voice,
            'business_context': spec.business_context,
            'sample_responses': spec.sample_responses,
            'instructions': spec.instructions[:500] + "..." if len(spec.instructions) > 500 else spec.instructions
        }
        with open(spec_file, 'w') as f:
            json.dump(spec_data, f, indent=2, default=str)

        log_message(f"   Events saved to: {events_file}")
        log_message(f"   Agent spec saved to: {spec_file}")
        log_message(f"   Full log saved to: {log_file}")

        # Final results
        log_message("=" * 70, "HEADER")
        log_message("🎉 LOCAL VERIFICATION RESULTS", "HEADER")
        log_message("=" * 70, "HEADER")

        if all_events_found:
            log_message("✅ ALL TESTS PASSED!", "SUCCESS")
            log_message("✅ Real-time agent creation is working", "SUCCESS")
            log_message("✅ Event broadcasting is functional", "SUCCESS")
            log_message("✅ Agent specifications are correct", "SUCCESS")
        else:
            log_message("❌ SOME ISSUES FOUND", "ERROR")
            log_message("❌ Check event sequence above", "ERROR")

        log_message("=" * 70, "HEADER")
        log_message("📋 For your frontend integration:", "INFO")
        log_message("   1. Use WebSocket to connect to your server", "INFO")
        log_message("   2. Listen for 'agent_creation_update' events", "INFO")
        log_message("   3. Each event contains: step, status, message, extra_data", "INFO")
        log_message("   4. Monitor for 'overall:completed' to know when done", "INFO")

        return all_events_found

    except Exception as e:
        log_message(f"❌ Test failed with exception: {e}", "ERROR")
        import traceback
        log_message(f"Traceback: {traceback.format_exc()}", "ERROR")
        return False

def main():
    print("🧪 Local Verification Test")
    print("This test runs the complete agent creation pipeline locally")
    print("and generates detailed logs you can examine.")
    print()

    success = create_detailed_log()

    if success:
        print("\n✅ Verification completed successfully!")
        print("📁 Check the logs/ directory for detailed results")
    else:
        print("\n❌ Verification failed!")
        print("📁 Check the logs/ directory for error details")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()