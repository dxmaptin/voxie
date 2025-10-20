import asyncio
from spawner import AgentLoader

async def quick_test():
    loader = AgentLoader()
    agent_id = "1034dd2a-8d7e-4e06-b1ba-853f02d7c157"
    
    config = await loader.load_agent_config(agent_id)
    if config:
        print(f"✅ SUCCESS! Found: {config.name}")
        print(f"   Voice: {config.voice}")
        print(f"   Prompt: {config.prompt_text[:]}...")
    else:
        print("❌ FAILED: Agent not found")

asyncio.run(quick_test())