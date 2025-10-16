# LiveKit Agent Spawner

Dedicated deployment for running user-created voice AI agents from the Supabase database.

## Purpose

This deployment **ONLY** runs agents that users have created via Voxie. It does NOT handle agent creation - that's Voxie's job.

## How It Works

1. **Room Pattern**: Only joins rooms matching `agent-*` pattern
2. **Agent Loading**: Extracts `agent_id` from room metadata or room name
3. **Dynamic Creation**: Loads agent config from Supabase and creates agent on-the-fly
4. **Execution**: Runs the agent with proper voice, instructions, and functions

## Setup

### 1. Install Dependencies

```bash
cd spawner
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local` with your credentials:
- LiveKit URL, API key, API secret (NEW instance from user)
- OpenAI API key
- Supabase URL and key

### 3. Run the Spawner

```bash
python spawner_agent.py
```

## Architecture

```
spawner/
├── spawner_agent.py           # Main entry point
├── agent_loader.py             # Loads agents from Supabase
├── dynamic_agent_factory.py    # Creates agents dynamically
├── requirements.txt            # Dependencies
├── .env.example                # Config template
└── README.md                   # This file
```

## Room Naming Convention

The spawner expects rooms to follow this pattern:

```
agent-{agent_id}-{random_suffix}
```

Example: `agent-123e4567-e89b-12d3-a456-426614174000-abc123`

The `agent_id` can also be provided in room metadata:

```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Separation from Voxie

| Feature | Voxie Deployment | Spawner Deployment |
|---------|------------------|-------------------|
| **Purpose** | Create agents | Run agents |
| **Room Pattern** | `voxie-creation-*` | `agent-*` |
| **Agent Type** | VoxieAgent only | Dynamic from DB |
| **Database** | Writes configs | Reads configs |
| **Scaling** | 1-2 instances | Multiple instances |

## Logging

The spawner logs extensively:
- Agent loading status
- Room connection details
- Session lifecycle events
- Analytics and transcription tracking

Look for these log markers:
- 🚀 Spawner starting
- 📥 Loading agent
- ✅ Agent created
- 🎵 Session started
- ⚠️ Warnings
- ❌ Errors

## Troubleshooting

### Agent Not Found
- Verify agent exists in Supabase `agents` table
- Check agent_id is correct UUID format
- Ensure Supabase credentials are valid

### Agent Won't Start
- Check LiveKit credentials
- Verify OpenAI API key
- Check logs for specific error messages

### Wrong Agent Joins Room
- Verify room name matches pattern `agent-*`
- Check no other deployments are running
- Ensure Voxie uses `voxie-creation-*` pattern

## Deployment

### Local Testing
```bash
python spawner_agent.py
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY spawner/ .
RUN pip install -r requirements.txt
CMD ["python", "spawner_agent.py"]
```

### Production (Systemd)
```ini
[Unit]
Description=LiveKit Agent Spawner
After=network.target

[Service]
Type=simple
User=spawner
WorkingDirectory=/opt/spawner
ExecStart=/usr/bin/python3 spawner_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring

Key metrics to track:
- Number of active agents
- Agent spawn success rate
- Session duration
- Error rates
- Resource usage (CPU/Memory per agent)

## Next Steps

1. Get new LiveKit credentials from user
2. Update `.env.local` with credentials
3. Test with existing agent from database
4. Deploy to production
5. Scale as needed
