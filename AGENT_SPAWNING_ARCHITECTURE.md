# Dynamic Agent Spawning Architecture

## Problem Statement

Currently, the Voxie system has an issue where **two agents join the same room**:
1. **Voxie** - The agent creator that collects requirements
2. **Custom Agent** - The dynamically created agent loaded from database

This causes conflicts and a poor user experience.

## Solution: Separate Deployments

Deploy **two independent LiveKit agent services** with clear separation of concerns.

---

## 🏗️ Architecture Design

```
┌────────────────────────────────────────────────────────────────────────┐
│                            USER FRONTEND                                │
│  • Dashboard UI for managing agents                                     │
│  • LiveKit client for voice interactions                                │
└────────────────────────────────────────────────────────────────────────┘
           │                                                    │
           │ HTTP/SSE                                           │ WebRTC
           ▼                                                    ▼
┌────────────────────────┐                    ┌────────────────────────────┐
│   BACKEND API          │                    │   LIVEKIT CLOUD            │
│   (Port 8000)          │                    │                            │
│                        │                    │  Room Management           │
│  • Agent CRUD          │                    │  Audio Streaming           │
│  • Analytics           │                    └────────────────────────────┘
│  • Spawn Control       │                             │           │
└────────────────────────┘                             │           │
           │                                            │           │
           │ Read/Write agents table                   │           │
           ▼                                            │           │
┌────────────────────────┐                             │           │
│   SUPABASE DATABASE    │                             │           │
│                        │                             │           │
│  • agents              │◄────────┐                   │           │
│  • call_sessions       │         │ Saves            │           │
│  • call_summaries      │         │ config           │           │
│  • token_usage         │         │                  │           │
└────────────────────────┘         │                  │           │
                                   │                  │           │
                                   │                  │           │
                         ┌─────────┴──────────────────▼───────────▼──────┐
                         │                                                │
                         │         SEPARATE AGENT DEPLOYMENTS             │
                         │                                                │
        ┌────────────────┴──────────────┐      ┌───────────────────────┴──┐
        │                               │      │                            │
        │  DEPLOYMENT 1: VOXIE          │      │  DEPLOYMENT 2: SPAWNER     │
        │  (Agent Creator)              │      │  (Dynamic Agent Runner)    │
        │                               │      │                            │
        │  voxie-test/src/agent.py      │      │  spawner/spawner_agent.py  │
        │  • Voxie conversation flow    │      │  • Loads agent by ID       │
        │  • Collects requirements      │      │  • Runs custom prompts     │
        │  • Creates agent configs      │      │  • Business-specific funcs │
        │  • Saves to Supabase          │      │  • Pure execution mode     │
        │  • NO agent spawning          │      │  • NO Voxie logic          │
        │                               │      │                            │
        │  LiveKit Room Pattern:        │      │  LiveKit Room Pattern:     │
        │  voxie-creation-*             │      │  agent-{agent_id}-*        │
        │                               │      │                            │
        │  Environment:                 │      │  Environment:              │
        │  DEPLOYMENT_MODE=voxie        │      │  DEPLOYMENT_MODE=spawner   │
        │  LIVEKIT_URL=...              │      │  LIVEKIT_URL=...           │
        │  LIVEKIT_API_KEY=...          │      │  LIVEKIT_API_KEY=...       │
        │                               │      │  AGENT_ID={from room meta} │
        └───────────────────────────────┘      └────────────────────────────┘
```

---

## 🎯 Key Design Principles

### 1. **Separation of Concerns**
- **Voxie Deployment**: ONLY handles agent creation conversations
- **Spawner Deployment**: ONLY runs user-created agents
- No overlap, no conflicts

### 2. **Room-Based Routing**
LiveKit agents can filter which rooms they join using room name patterns:

```python
# Voxie deployment - only joins creation rooms
agents.cli.run_app(agents.WorkerOptions(
    entrypoint_fnc=voxie_entrypoint,
    room_name_pattern="voxie-creation-*"  # Only join these rooms
))

# Spawner deployment - only joins agent execution rooms
agents.cli.run_app(agents.WorkerOptions(
    entrypoint_fnc=spawner_entrypoint,
    room_name_pattern="agent-*"  # Only join these rooms
))
```

### 3. **Database-Driven Configuration**
- Voxie saves agent configs to Supabase `agents` table
- Spawner reads agent ID from room metadata
- Spawner loads full configuration from database
- Zero hardcoding needed

---

## 📋 Implementation Plan

### **Phase 1: Split the Code**

**File Structure:**
```
voxie-clean/
├── voxie-test/
│   └── src/
│       └── agent.py                    # Existing Voxie (keep as is)
│
├── spawner/                            # NEW - Spawner deployment
│   ├── spawner_agent.py                # Main spawner logic
│   ├── agent_loader.py                 # Load agents from DB
│   ├── dynamic_agent_factory.py        # Create agents dynamically
│   └── requirements.txt                # Dependencies
│
├── backend_server.py                   # Backend API
└── agent_dashboard.html                # Dashboard UI
```

### **Phase 2: Create Spawner Service**

**spawner/spawner_agent.py** - The new deployment:

```python
"""
LiveKit Agent Spawner - Dynamically runs agents from database
This deployment ONLY runs user-created agents, never Voxie
"""

import os
import logging
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import openai, noise_cancellation
from agent_loader import AgentLoader
from dynamic_agent_factory import DynamicAgentFactory

logger = logging.getLogger("spawner")

async def spawner_entrypoint(ctx: agents.JobContext):
    """
    Spawner entry point - loads and runs a specific agent

    How it works:
    1. Extract agent_id from room metadata
    2. Load agent config from Supabase
    3. Create agent dynamically from config
    4. Start session with the agent
    """

    # Get agent ID from room metadata
    agent_id = ctx.room.metadata.get("agent_id")

    if not agent_id:
        logger.error("❌ No agent_id in room metadata")
        return

    logger.info(f"🚀 Spawner starting agent: {agent_id}")

    # Load agent configuration from database
    agent_config = await AgentLoader.load_agent(agent_id)

    if not agent_config:
        logger.error(f"❌ Agent {agent_id} not found in database")
        return

    logger.info(f"✅ Loaded: {agent_config['name']}")

    # Create the agent dynamically
    agent = DynamicAgentFactory.create_from_config(agent_config)

    # Start session
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice=agent_config['voice'])
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Greet the user
    greeting = agent_config.get('greeting') or f"Hello! I'm {agent_config['name']}. How can I help you?"
    await session.generate_reply(instructions=f"Say: {greeting}")

    logger.info(f"✅ Agent {agent_id} active in room {ctx.room.name}")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=spawner_entrypoint,
        room_name_pattern="agent-*",  # Only join agent rooms
        num_idle_processes=1
    ))
```

### **Phase 3: Modify Voxie Deployment**

**voxie-test/src/agent.py** - Remove spawning logic:

```python
# REMOVE the start_specific_agent() function entirely
# REMOVE the AGENT_ID checking logic from entrypoint()

async def entrypoint(ctx: agents.JobContext):
    """Main entry point - ONLY starts Voxie (agent creator)"""

    # NO MORE: if agent_id: await start_specific_agent(...)

    # ALWAYS start with Voxie
    logger.info("Starting Voxie - Agent Creation System")

    # ... rest of Voxie logic stays the same
```

Update the CLI to use room pattern:

```python
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        room_name_pattern="voxie-creation-*",  # Only join creation rooms
        num_idle_processes=0
    ))
```

### **Phase 4: Update Backend API**

Add endpoint to spawn agents:

```python
from pydantic import BaseModel
import aiohttp

class SpawnAgentRequest(BaseModel):
    agent_id: str
    user_token: Optional[str] = None  # LiveKit token for user

@app.post("/api/agents/{agent_id}/spawn")
async def spawn_agent(agent_id: str, request: SpawnAgentRequest):
    """
    Create a LiveKit room for the agent and return connection details
    """
    try:
        # Verify agent exists
        from supabase_client import supabase_client
        agent = supabase_client.client.table('agents')\
            .select('*')\
            .eq('id', agent_id)\
            .single()\
            .execute()

        if not agent.data:
            raise HTTPException(404, "Agent not found")

        # Create LiveKit room with agent_id in metadata
        room_name = f"agent-{agent_id}-{uuid.uuid4().hex[:8]}"

        # Use LiveKit API to create room with metadata
        from livekit import api
        livekit_api = api.LiveKitAPI(
            url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )

        # Create room
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=json.dumps({"agent_id": agent_id})
            )
        )

        # Generate user token
        token = api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET")
        )
        token.with_identity("user")
        token.with_name("User")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name
        ))
        user_token = token.to_jwt()

        return {
            "status": "success",
            "room_name": room_name,
            "token": user_token,
            "livekit_url": os.getenv("LIVEKIT_URL"),
            "agent": agent.data
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to spawn agent: {str(e)}")
```

### **Phase 5: Update Dashboard**

Add "Test Agent" button that calls spawn API:

```javascript
async function testAgent(agentId) {
    try {
        // Call backend to create room and spawn agent
        const response = await fetch(`${API_BASE}/api/agents/${agentId}/spawn`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Connect to LiveKit room
            const room = new LiveKitClient.Room();
            await room.connect(data.livekit_url, data.token);

            // Enable microphone
            await room.localParticipant.setMicrophoneEnabled(true);

            showSuccess(`Connected to ${data.agent.name}!`);
        }
    } catch (error) {
        showError('Failed to test agent: ' + error.message);
    }
}
```

---

## 🚀 Deployment Strategy

### **Option A: Single Server, Multiple Processes**

Run both deployments on same server:

```bash
# Terminal 1 - Voxie deployment
cd voxie-test/src
python agent.py

# Terminal 2 - Spawner deployment
cd spawner
python spawner_agent.py

# Terminal 3 - Backend API
python backend_server.py
```

### **Option B: Separate Servers (Recommended for Production)**

```
Server 1 (Voxie):
- voxie-test/src/agent.py
- Handles voxie-creation-* rooms
- Lower resource requirements

Server 2 (Spawner):
- spawner/spawner_agent.py
- Handles agent-* rooms
- Auto-scales based on agent usage
- Can run multiple instances

Server 3 (Backend):
- backend_server.py
- Stateless API
- Can scale horizontally
```

### **Option C: Docker Containers**

```yaml
# docker-compose.yml
services:
  voxie:
    build: ./voxie-test
    environment:
      - DEPLOYMENT_MODE=voxie
      - LIVEKIT_URL=${LIVEKIT_URL}

  spawner:
    build: ./spawner
    environment:
      - DEPLOYMENT_MODE=spawner
      - LIVEKIT_URL=${LIVEKIT_URL}
    deploy:
      replicas: 3  # Multiple instances for scaling

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
```

---

## 🔄 How It Works End-to-End

### **Scenario 1: Creating an Agent**

1. User opens dashboard → clicks "Create New Agent"
2. Frontend creates LiveKit room: `voxie-creation-abc123`
3. **Voxie deployment** joins (room pattern match)
4. User talks to Voxie, describes their needs
5. Voxie saves agent config to Supabase → gets `agent_id`
6. User ends session

### **Scenario 2: Testing an Agent**

1. User clicks "Test Agent" on dashboard
2. Frontend calls `POST /api/agents/{agent_id}/spawn`
3. Backend:
   - Creates room: `agent-{agent_id}-xyz789`
   - Sets room metadata: `{"agent_id": "..."}`
   - Generates user token
   - Returns connection info
4. **Spawner deployment** joins (room pattern match)
5. Spawner reads agent_id from metadata
6. Spawner loads config from Supabase
7. Spawner creates dynamic agent
8. User talks to their custom agent
9. **Voxie never involved** - completely separate

---

## ✅ Benefits of This Approach

1. **No Conflicts**: Voxie and spawned agents never in same room
2. **Scalable**: Spawner can run multiple instances
3. **Flexible**: Easy to add new agent types
4. **Database-Driven**: All config in Supabase, zero hardcoding
5. **Production-Ready**: Clear separation of concerns
6. **Easy Testing**: Can test each deployment independently

---

## 🛠️ Implementation Checklist

- [ ] Create `spawner/` directory structure
- [ ] Implement `spawner_agent.py` with room pattern filtering
- [ ] Implement `agent_loader.py` to fetch from Supabase
- [ ] Implement `dynamic_agent_factory.py` to create agents
- [ ] Update `voxie-test/src/agent.py` to remove spawning logic
- [ ] Add room pattern filtering to Voxie deployment
- [ ] Add `/api/agents/{id}/spawn` endpoint to backend
- [ ] Update dashboard with "Test Agent" functionality
- [ ] Test both deployments independently
- [ ] Test end-to-end flow: create → save → spawn → test
- [ ] Deploy to production servers
- [ ] Set up monitoring and logging

---

## 📊 Monitoring & Debugging

### **Check Which Deployment Joined a Room**

```python
# Add to both deployments
logger.info(f"🏷️ Deployment: {os.getenv('DEPLOYMENT_MODE')}")
logger.info(f"🏠 Room: {ctx.room.name}")
logger.info(f"📋 Metadata: {ctx.room.metadata}")
```

### **LiveKit Dashboard**

- View active rooms
- See which agents are connected
- Monitor resource usage per deployment

---

## 🔮 Future Enhancements

1. **Agent Versioning**: Track agent config changes over time
2. **A/B Testing**: Run multiple versions of same agent
3. **Load Balancing**: Distribute agents across spawner instances
4. **Agent Pools**: Pre-warm agents for faster startup
5. **Graceful Shutdown**: Properly handle agent updates without dropping calls
6. **Analytics**: Track performance per agent deployment

---

## 💡 Summary

**Two deployments, two purposes:**

| Deployment | Purpose | Room Pattern | Scalability |
|------------|---------|--------------|-------------|
| **Voxie** | Create agents | `voxie-creation-*` | Low (1-2 instances) |
| **Spawner** | Run agents | `agent-*` | High (auto-scale) |

**Clean separation = No conflicts = Production ready** ✅
