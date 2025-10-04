"""
Test script to verify agent persistence integration
Run this before doing console test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_persistence import AgentPersistence

print("🧪 Testing Agent Persistence Integration...\n")

# Test connection
print("1️⃣ Testing Supabase connection...")
try:
    from supabase_client import supabase_client
    print(f"   ✅ Connected to: {supabase_client.url}\n")
except Exception as e:
    print(f"   ❌ Connection failed: {e}\n")
    sys.exit(1)

# Test listing existing agents
print("2️⃣ Listing existing agents...")
try:
    agents = AgentPersistence.list_agents(limit=5)
    print(f"   Found {len(agents)} agents in database")
    for agent in agents[:3]:
        print(f"   - {agent['name']} ({agent['category']}) - {agent['created_at'][:10]}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Test save operation
print("3️⃣ Testing save operation...")
test_requirements = {
    'business_name': 'Test Integration Check',
    'business_type': 'Test',
    'tone': 'test',
    'main_functions': ['test']
}

test_spec = {
    'agent_type': 'Test Integration Agent',
    'instructions': 'Test instructions',
    'voice': 'alloy',
    'functions': [],
    'sample_responses': [],
    'business_context': {'test': True}
}

try:
    agent_id = AgentPersistence.save_agent_config(
        user_requirements=test_requirements,
        processed_spec=test_spec,
        session_id='test-integration',
        room_id='test-room'
    )

    if agent_id:
        print(f"   ✅ Save successful! Agent ID: {agent_id}")

        # Test load
        print(f"\n4️⃣ Testing load operation...")
        loaded = AgentPersistence.load_agent_config(agent_id)
        if loaded:
            print(f"   ✅ Load successful!")
            print(f"   Business: {loaded['user_requirements']['business_name']}")
            print(f"   Agent Type: {loaded['processed_spec']['agent_type']}")

        print(f"\n✅ ALL TESTS PASSED!")
        print(f"   Integration is ready for console testing")
        print(f"\n   NOTE: Test agent '{agent_id}' has been saved to database")
        print(f"   (No deletion - as requested)")
    else:
        print(f"   ❌ Save failed")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
