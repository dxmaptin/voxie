# Exercise 3: Quick Start - Deploy to LiveKit Cloud

## TL;DR

Deploy your agent to LiveKit Cloud in 3 commands:

```bash
cd voxie-test
lk cloud auth
lk agent create
```

Your agent will automatically join rooms when they're created!

## What's Been Prepared

All configuration files are ready for deployment:

✅ **Dockerfile** - Optimized for cloud deployment
✅ **livekit.toml** - Agent configuration (will be populated)
✅ **.env.production.example** - Template for environment variables
✅ **.dockerignore** - Excludes unnecessary files
✅ **pyproject.toml** - Python dependencies

## Prerequisites

1. **LiveKit CLI** installed:
   ```bash
   brew install livekit-cli  # macOS
   # or: curl -sSL https://get.livekit.io/cli | bash
   ```

2. **LiveKit Cloud account**: https://cloud.livekit.io

3. **API Keys ready**:
   - OPENAI_API_KEY
   - SUPABASE_URL + SUPABASE_ANON_KEY

## Deployment Steps

### 1. Authenticate

```bash
cd voxie-test
lk cloud auth
```

### 2. Create Agent

```bash
lk agent create
```

This will:
- Build Docker image
- Upload to LiveKit Cloud
- Deploy the agent
- Update livekit.toml

### 3. Set Environment Variables

Go to https://cloud.livekit.io:
1. Select your project
2. Go to **Agents** → Your agent → **Settings**
3. Add environment variables:

```
OPENAI_API_KEY=sk-proj-your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
```

4. Click **Save** and **Redeploy**

### 4. Verify Deployment

```bash
# Check status
lk agent status

# View logs
lk agent logs --follow
```

## Testing

### Option 1: Use Exercise 2 Interface

```bash
# From voxie root directory
python backend_server.py

# Open browser: http://localhost:8000/call
# Select agent and start call
# Agent joins automatically from LiveKit Cloud!
```

### Option 2: Use LiveKit Playground

1. Go to: https://agents-playground.livekit.io
2. Enter your LiveKit URL: `wss://your-project.livekit.cloud`
3. Create test token:
   ```bash
   lk token create --join --room test-room
   ```
4. Connect - agent auto-joins!

## Updating After Changes

```bash
# Make code changes
# Then deploy:
lk agent deploy
```

Rolling deployment with zero downtime!

## Monitoring

```bash
# View status
lk agent status

# Stream logs
lk agent logs --follow

# Filter errors
lk agent logs --level error
```

## Common Issues

### "Agent not found"
```bash
# Re-authenticate
lk cloud auth
lk project list
```

### "Build failed"
```bash
# Test local build
docker build -t test-agent .

# Check dependencies
cat pyproject.toml
```

### "Agent not joining rooms"
```bash
# Check status
lk agent status

# View logs
lk agent logs

# Verify environment variables in dashboard
```

## Architecture Change

**Before (Exercise 2):**
- Backend spawns local agent process per call
- Agent runs on your machine

**After (Exercise 3):**
- LiveKit Cloud auto-dispatches agents
- Agent runs in cloud container
- No manual spawning needed!

## Key Differences

| Aspect | Local (Ex 2) | Cloud (Ex 3) |
|--------|-------------|--------------|
| Agent Location | Your machine | LiveKit Cloud |
| Startup | Manual spawn | Auto-dispatch |
| Scaling | Manual | Automatic |
| Monitoring | Local logs | Cloud dashboard |
| Reliability | Depends on your machine | High availability |
| Cost | Free (your machine) | Pay for usage |

## Next Steps

1. **Remove local agent spawning** (optional):
   In `backend_server.py`, comment out subprocess spawning since cloud handles it

2. **Monitor usage** in LiveKit Cloud dashboard

3. **Set up alerts** for failures

4. **Optimize costs** by monitoring agent runtime

## Success Criteria

Exercise 3 is complete when:
- ✅ `lk agent status` shows "Running"
- ✅ Agent automatically joins when you create a room
- ✅ Exercise 2 call interface works with cloud agent
- ✅ No manual agent spawning required

## Files Modified

**Updated:**
- `voxie-test/Dockerfile` - Fixed CMD for cloud
- `voxie-test/.dockerignore` - Updated exclusions
- `voxie-test/livekit.toml` - Template format

**Created:**
- `voxie-test/.env.production.example` - Production env template
- `voxie-test/EXERCISE_3_DEPLOYMENT_GUIDE.md` - Full guide
- `voxie-test/EXERCISE_3_QUICKSTART.md` - This file

**Unchanged:**
- `voxie-test/src/agent.py` - Works as-is!
- `voxie-test/pyproject.toml` - Already configured
- All other source files

## Command Reference

```bash
# Deployment
lk cloud auth                    # Authenticate
lk agent create                  # Create + deploy
lk agent deploy                  # Update deployment
lk agent rollback                # Revert version

# Monitoring
lk agent status                  # Check health
lk agent logs                    # View logs
lk agent logs --follow           # Stream logs

# Management
lk agent scale --replicas N      # Scale manually
lk agent delete                  # Delete agent
lk project list                  # List projects
```

## Need Help?

1. **Check logs**: `lk agent logs`
2. **Read full guide**: `EXERCISE_3_DEPLOYMENT_GUIDE.md`
3. **LiveKit Docs**: https://docs.livekit.io/agents/
4. **Dashboard**: https://cloud.livekit.io

---

**You're ready to deploy!** Run `lk agent create` and your agent goes live.
