# Exercise 3: Deploy Agent to LiveKit Cloud

## Goal

Deploy your Voxie agent to LiveKit Cloud using Agent Dispatch so that agents automatically start when a room is created.

## Overview

LiveKit Cloud provides managed agent hosting with:
- **Auto-dispatch**: Agents automatically join rooms when created
- **Auto-scaling**: Scales based on demand
- **Rolling deployments**: Zero-downtime updates
- **Monitoring**: Built-in logs and health checks
- **No infrastructure management**: Fully managed service

## Architecture

```
Browser/Client                  LiveKit Cloud                    Your Agent (Deployed)
     |                               |                                    |
     |-- Create Room --------------->|                                    |
     |                               |                                    |
     |                               |-- Auto-dispatch Agent ------------>|
     |                               |                                    |
     |<-- Room Created + Token ------|                                    |
     |                               |                                    |
     |-- Connect with Token -------->|                                    |
     |                               |<-- Agent Connects -----------------|
     |                               |                                    |
     |<-- Bidirectional Audio ----------------------------------->|       |
```

## Prerequisites

### 1. Install LiveKit CLI

```bash
# macOS
brew install livekit-cli

# Linux/WSL
curl -sSL https://get.livekit.io/cli | bash

# Or download from: https://github.com/livekit/livekit-cli/releases
```

Verify installation:
```bash
lk --version
```

### 2. LiveKit Cloud Account

1. Sign up at https://cloud.livekit.io
2. Create a new project or use existing one
3. Note your project subdomain (e.g., `my-project-xyz123.livekit.cloud`)

### 3. Prepare Environment Variables

You'll need these API keys:
- **OPENAI_API_KEY** (required for voice)
- **SUPABASE_URL** and **SUPABASE_ANON_KEY** (required for database)
- **DEEPGRAM_API_KEY** (optional, for transcription)
- **ANTHROPIC_API_KEY** (optional, for summaries)

## Step-by-Step Deployment

### Step 1: Authenticate with LiveKit Cloud

```bash
# Navigate to the voxie-test directory
cd voxie-test

# Authenticate with LiveKit Cloud
lk cloud auth
```

This will:
- Open your browser for authentication
- Link your CLI to your LiveKit Cloud account
- Save credentials locally

Verify authentication:
```bash
# List your projects
lk project list

# Set default project (if you have multiple)
lk project set-default "your-project-name"
```

### Step 2: Create and Register Your Agent

```bash
# From voxie-test directory
lk agent create
```

This command will:
1. Assign a unique agent ID
2. Update `livekit.toml` with your project subdomain and agent ID
3. Create Dockerfile if it doesn't exist (we already have one)
4. Build Docker image
5. Upload to LiveKit Cloud
6. Deploy the agent

**Example output:**
```
✓ Agent created successfully
  Agent ID: CA_abc123def456
  Project: my-project-xyz123
  Subdomain: my-project-xyz123.livekit.cloud

✓ Building Docker image...
✓ Uploading image to LiveKit Cloud...
✓ Deploying agent...
✓ Agent deployed successfully!

Your agent is now live and will auto-start when rooms are created.
```

### Step 3: Configure Environment Variables in LiveKit Cloud

**Option A: Using LiveKit Cloud Dashboard (Recommended for Production)**

1. Go to https://cloud.livekit.io
2. Select your project
3. Navigate to **Agents** section
4. Click on your agent
5. Go to **Settings** → **Environment Variables**
6. Add the following variables:

```
OPENAI_API_KEY=sk-proj-your-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
DEEPGRAM_API_KEY=your-deepgram-key (optional)
ANTHROPIC_API_KEY=sk-ant-your-key (optional)
```

7. Save and redeploy

**Option B: Using .env File (For Testing)**

Create `.env` in `voxie-test` directory:
```bash
# Copy the example file
cp .env.production.example .env

# Edit with your actual keys
nano .env
```

**Note**: LiveKit Cloud automatically provides `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` - you don't need to set these.

### Step 4: Deploy Updates (After Changes)

After making code changes:

```bash
# Deploy updated version
lk agent deploy
```

This will:
- Build new Docker image
- Upload to LiveKit Cloud
- Perform rolling deployment (zero downtime)
- Keep old instances running for up to 1 hour for active sessions
- Route new sessions to new instances

### Step 5: Verify Deployment

Check agent status:
```bash
# View agent status
lk agent status

# Stream live logs
lk agent logs

# Follow logs (like tail -f)
lk agent logs --follow
```

**Expected output:**
```
✓ Agent Status
  Agent ID: CA_abc123def456
  Status: Running
  Replicas: 1/1 healthy
  Version: v2 (deployed 5 minutes ago)
  Last deployment: 2025-01-17 10:30:00 UTC
```

## Testing the Deployment

### Test 1: Using Simple Call Interface (Exercise 2)

1. **Start your backend server** (locally):
   ```bash
   cd ..  # Go back to voxie root
   python backend_server.py
   ```

2. **Open the call interface**:
   ```
   http://localhost:8000/call
   ```

3. **Make a call**:
   - Select an agent
   - Click "Start Call"
   - **The agent should automatically join from LiveKit Cloud!**
   - Speak and verify the agent responds

4. **Check logs** (in separate terminal):
   ```bash
   cd voxie-test
   lk agent logs --follow
   ```

   You should see:
   ```
   🚀 Starting agent...
   ✅ Connected to LiveKit Cloud
   🎯 Waiting for rooms...
   📞 Joining room: call_abc123_xyz789
   ✅ Agent active in room
   ```

### Test 2: Using LiveKit Playground

1. Go to https://agents-playground.livekit.io
2. Enter your LiveKit Cloud URL: `wss://your-project.livekit.cloud`
3. Use a test token or create one:
   ```bash
   lk token create --join --room test-room
   ```
4. Connect to a room
5. **Your agent should automatically join!**
6. Test voice interaction

### Test 3: Direct API Call

Create a room via API and verify agent auto-joins:

```bash
# Create a room (agent should auto-dispatch)
curl -X POST https://your-project.livekit.cloud/twirp/livekit.RoomService/CreateRoom \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-room-123"}'

# Check agent logs
lk agent logs --follow
```

## Monitoring and Management

### View Agent Status

```bash
# Quick status check
lk agent status

# Detailed info
lk agent status --verbose
```

### View Live Logs

```bash
# Stream logs
lk agent logs

# Follow logs (continuous)
lk agent logs --follow

# Filter logs by level
lk agent logs --level error

# Show last N lines
lk agent logs --tail 100
```

### Scaling

LiveKit Cloud automatically scales based on demand:
- **1 agent replica** for low traffic
- **Multiple replicas** during peak times
- **Scales down** when idle

Manual scaling (if needed):
```bash
# Scale to specific number of replicas
lk agent scale --replicas 3
```

### Rollback (Paid Plans Only)

If deployment has issues:
```bash
# Rollback to previous version
lk agent rollback

# Rollback to specific version
lk agent rollback --version v5
```

## Configuration Files

### 1. **Dockerfile** (voxie-test/Dockerfile)

Updated for cloud deployment:
- Uses `uv` for fast dependency management
- Multi-stage build for smaller images
- Non-root user for security
- Clean, optimized layers

```dockerfile
CMD ["uv", "run", "python", "src/agent.py"]
```

### 2. **livekit.toml** (voxie-test/livekit.toml)

Configuration file automatically populated by `lk agent create`:

```toml
[project]
  subdomain = "your-project-xyz123"

[agent]
  id = "CA_abc123def456"
```

### 3. **.dockerignore** (voxie-test/.dockerignore)

Excludes unnecessary files from Docker image:
- Local environment files (`.env.local`)
- Virtual environments (`.venv/`)
- Cache files
- Tests
- Git files

### 4. **.env.production.example**

Template for environment variables needed in production.

### 5. **pyproject.toml** (voxie-test/pyproject.toml)

Python dependencies managed by `uv`:
```toml
dependencies = [
    "livekit-agents[openai,turn-detector,silero,cartesia,deepgram]~=1.2",
    "livekit-plugins-noise-cancellation~=0.2",
    "python-dotenv",
    "supabase~=2.0",
    ...
]
```

## Architecture: How Agent Dispatch Works

### Auto-Dispatch Flow

1. **Agent Deployment**:
   - Docker container built and uploaded
   - Registered with LiveKit Cloud
   - Agent ID assigned
   - Container stays running, waiting for rooms

2. **Room Creation**:
   - Client/backend creates a room via API or frontend
   - LiveKit Cloud detects new room

3. **Agent Auto-Dispatch**:
   - LiveKit Cloud automatically dispatches available agent
   - Agent receives room assignment
   - Agent joins room via `JobContext`

4. **Session Handling**:
   - Agent establishes WebRTC connection
   - Handles audio streams
   - Executes conversation logic
   - Exits when room ends

5. **Cleanup**:
   - Agent disconnects from room
   - Returns to waiting state
   - Ready for next room assignment

### Code Flow (src/agent.py)

```python
async def entrypoint(ctx: agents.JobContext):
    """
    Main entry point - called by LiveKit when dispatching agent

    ctx.room: The LiveKit room to join
    ctx.job: Job metadata and configuration
    """
    # Agent automatically joins the room provided in ctx
    # No manual room selection needed!

    # Start agent logic...
    agent_manager.room = ctx.room

    # Start session
    session = AgentSession(...)
    await session.start(room=ctx.room, agent=VoxieAgent())

    # Agent is now active and handling the call

# This runs when container starts
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        num_idle_processes=0
    ))
```

## Troubleshooting

### Agent Not Deploying

**Problem**: `lk agent create` fails

**Solutions**:
```bash
# Check authentication
lk cloud auth

# Verify Docker is running
docker --version
docker ps

# Check Dockerfile syntax
docker build -t test-agent .

# View detailed error logs
lk agent create --verbose
```

### Agent Not Joining Rooms

**Problem**: Room created but agent doesn't join

**Solutions**:

1. **Check agent status**:
   ```bash
   lk agent status
   ```
   Should show "Running" and healthy replicas

2. **Check logs**:
   ```bash
   lk agent logs --follow
   ```
   Look for connection errors

3. **Verify environment variables**:
   - Check LiveKit Cloud dashboard → Agents → Settings → Environment Variables
   - Ensure OPENAI_API_KEY is set
   - Ensure SUPABASE credentials are correct

4. **Test locally first**:
   ```bash
   cd voxie-test
   python src/agent.py
   ```
   Should connect to LiveKit and wait for jobs

### Build Failures

**Problem**: Docker build fails during `lk agent deploy`

**Solutions**:

1. **Check dependencies** in `pyproject.toml`
2. **Test local build**:
   ```bash
   docker build -t voxie-agent .
   ```
3. **Check uv.lock** file is committed
4. **Verify Python version** matches Dockerfile (3.11)

### Connection Timeouts

**Problem**: Agent connects but times out

**Solutions**:

1. Check LiveKit URL is correct: `wss://` not `ws://`
2. Verify API credentials in environment variables
3. Check network/firewall settings
4. Review logs for WebSocket errors:
   ```bash
   lk agent logs | grep -i "websocket\|connection\|timeout"
   ```

### Missing API Keys

**Problem**: Agent fails with authentication errors

**Solutions**:

1. Set environment variables in LiveKit Cloud dashboard
2. Verify keys are valid:
   ```bash
   # Test OpenAI key
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"

   # Test Supabase connection
   curl "$SUPABASE_URL/rest/v1/" \
     -H "apikey: $SUPABASE_ANON_KEY"
   ```
3. Redeploy after adding keys:
   ```bash
   lk agent deploy
   ```

## Best Practices

### 1. Environment Management

- **Never commit `.env` files** with real secrets
- Use `.env.production.example` as template
- Set secrets in LiveKit Cloud dashboard for production
- Use different API keys for dev/staging/production

### 2. Deployment Strategy

- **Test locally first** before deploying
- Use `lk agent logs --follow` during deployment
- Deploy during low-traffic periods
- Monitor logs for first few minutes after deployment
- Keep old versions available for rollback

### 3. Monitoring

- Set up alerts in LiveKit Cloud dashboard
- Monitor agent health regularly: `lk agent status`
- Check logs daily for errors: `lk agent logs --level error`
- Track room connection rates
- Monitor costs and usage

### 4. Security

- Use non-root user in Docker (already configured)
- Keep dependencies updated: `uv lock --upgrade`
- Rotate API keys regularly
- Use least-privilege API keys when possible
- Enable rate limiting in LiveKit dashboard

### 5. Performance

- Keep Docker images small (use `.dockerignore`)
- Pre-load models if needed
- Optimize agent startup time
- Use connection pooling for database
- Cache frequently accessed data

## Cost Optimization

LiveKit Cloud pricing is based on:
- **Agent runtime hours**
- **Bandwidth usage**
- **Concurrent sessions**

Tips to reduce costs:
1. Use auto-scaling (default)
2. Agents exit promptly when rooms end
3. Optimize Docker image size
4. Use efficient audio codecs
5. Monitor usage in dashboard

## Next Steps

Now that your agent is deployed:

### 1. Update Exercise 2 to Use Cloud Agent

Modify `backend_server.py` to use LiveKit Cloud URLs:

```python
# In /api/call/start endpoint
livekit_url = os.getenv("LIVEKIT_URL")  # Already cloud URL
```

No changes needed! Exercise 2 works automatically with cloud agents.

### 2. Remove Local Agent Spawning

Since agents auto-dispatch from cloud, remove subprocess spawning:

```python
# In backend_server.py - OPTIONAL: Comment out local agent spawning
# subprocess.Popen(['python3', 'simple_agent.py'], ...)
```

Agents now start automatically from cloud when rooms are created.

### 3. Monitor Production Usage

- Set up alerts for failures
- Track call quality metrics
- Monitor agent response times
- Review logs for errors

### 4. Scale as Needed

LiveKit Cloud auto-scales, but you can:
- Adjust replica counts manually if needed
- Deploy to multiple regions (paid plans)
- Set custom scaling policies

## Exercise 3 Complete! ✅

You have successfully:
- [x] Prepared agent code for cloud deployment
- [x] Updated Dockerfile and configuration files
- [x] Deployed agent to LiveKit Cloud
- [x] Configured auto-dispatch on room creation
- [x] Tested agent automatically joins rooms
- [x] Set up monitoring and logging

### Success Criteria

Exercise 3 is complete when:
- [x] `lk agent status` shows "Running"
- [x] Agent automatically joins when room is created
- [x] Exercise 2 call interface works with cloud agent
- [x] Logs show agent connecting and handling calls
- [x] No manual agent spawning required

**Your Voxie agent now runs on LiveKit Cloud and automatically handles voice calls!**

---

## Quick Command Reference

```bash
# Authentication
lk cloud auth                    # Authenticate with LiveKit Cloud
lk project list                  # List projects
lk project set-default "name"    # Set default project

# Deployment
lk agent create                  # Create and deploy new agent
lk agent deploy                  # Deploy code updates
lk agent rollback                # Rollback to previous version

# Monitoring
lk agent status                  # Check agent health
lk agent logs                    # View logs
lk agent logs --follow           # Stream logs live
lk agent logs --level error      # Filter by level

# Management
lk agent scale --replicas 3      # Manual scaling
lk agent delete                  # Delete agent
lk agent list                    # List all agents

# Testing
lk token create --join --room test  # Create test token
```

---

For more information:
- LiveKit Agents Docs: https://docs.livekit.io/agents/
- LiveKit Cloud Dashboard: https://cloud.livekit.io
- LiveKit CLI: https://github.com/livekit/livekit-cli
