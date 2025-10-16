# LiveKit Agent Deployment Fix

## Problem

Error when running `lk agent create`:
```
Using project [voxie-1]
project does not match agent subdomain []
```

## Root Cause

The `livekit.toml` file had an empty `subdomain = ""` field, which didn't match your selected project `voxie-1`.

## Solution Applied

### 1. Updated livekit.toml

**File**: `voxie-test/livekit.toml`

**Changed from:**
```toml
[project]
  subdomain = ""

[agent]
  id = ""
```

**Changed to:**
```toml
[project]
  subdomain = "voxie-1-f00463v2"

[agent]
  id = ""
```

The subdomain `voxie-1-f00463v2` matches your LiveKit Cloud project URL:
`wss://voxie-1-f00463v2.livekit.cloud`

## Step-by-Step Deployment

### Prerequisites Check

```bash
# 1. Verify you're in the correct directory
cd /Users/muhammad/Personal/Projects/Personal\ Projects/Voxie/voxie/voxie-test
pwd
# Should show: /Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie/voxie-test

# 2. Verify LiveKit CLI is authenticated
lk project list
# Should show voxie-1 with * (selected)

# 3. Verify livekit.toml is correct
cat livekit.toml
# Should show subdomain = "voxie-1-f00463v2"
```

### Deployment Commands

```bash
# From voxie-test directory:
cd /Users/muhammad/Personal/Projects/Personal\ Projects/Voxie/voxie/voxie-test

# Create and deploy agent
lk agent create
```

**Expected Output:**
```
✓ Using project [voxie-1]
✓ Building Docker image...
✓ Uploading image to LiveKit Cloud...
✓ Creating agent...
✓ Agent created successfully

Agent ID: CA_xxxxxxxxx
Project: voxie-1
Subdomain: voxie-1-f00463v2.livekit.cloud
Status: Deploying...
```

The `livekit.toml` will be automatically updated with the agent ID:
```toml
[project]
  subdomain = "voxie-1-f00463v2"

[agent]
  id = "CA_xxxxxxxxx"  # Automatically filled
```

### If You Still Get Errors

#### Error: "project does not match"

**Fix:**
```bash
# Re-authenticate
lk cloud auth

# Ensure voxie-1 is default project
lk project set-default voxie-1

# Verify
lk project list
# Should show * next to voxie-1

# Try again
lk agent create
```

#### Error: "Docker build failed"

**Fix:**
```bash
# Test Docker build locally
docker build -t test-agent .

# Check Docker is running
docker ps

# If Docker not running, start Docker Desktop
```

#### Error: "Missing environment variables"

**Fix:**
You'll need to set environment variables in LiveKit Cloud dashboard AFTER the agent is created.

1. Go to: https://cloud.livekit.io
2. Select project: `voxie-1`
3. Go to: **Agents** → Your agent → **Settings** → **Environment Variables**
4. Add:
   ```
   OPENAI_API_KEY=sk-proj-your-key
   SUPABASE_URL=https://gkfuepzqdzixejspfrlg.supabase.co
   SUPABASE_ANON_KEY=your-supabase-key
   ```
5. Click **Save** and **Redeploy**

## Testing the Deployment

### Step 1: Verify Agent Status

```bash
# Check agent status
lk agent status

# Expected output:
# ✓ Agent Status
#   Agent ID: CA_xxxxxxxxx
#   Status: Running
#   Replicas: 1/1 healthy
#   Project: voxie-1
```

### Step 2: Watch Logs

```bash
# Stream live logs
lk agent logs --follow

# Expected output:
# 🚀 Starting agent...
# ✅ Connected to LiveKit Cloud
# 🎯 Waiting for rooms...
```

### Step 3: Test with Exercise 2 Interface

```bash
# In a new terminal, start backend server
cd /Users/muhammad/Personal/Projects/Personal\ Projects/Voxie/voxie
python backend_server.py

# Open browser: http://localhost:8000/call
# Select an agent
# Click "Start Call"
```

**Expected behavior:**
1. Browser creates room
2. Cloud agent automatically joins (check logs with `lk agent logs --follow`)
3. You can speak and agent responds
4. Agent exits when call ends

### Step 4: Test Direct Room Creation

```bash
# Create a test room
curl -X POST "https://voxie-1-f00463v2.livekit.cloud/twirp/livekit.RoomService/CreateRoom" \
  -H "Authorization: Bearer $(lk token create --room test-room-$(date +%s))" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-room"}'

# Watch agent join
lk agent logs --follow
```

You should see in logs:
```
📞 Joining room: test-room
✅ Agent active in room
```

## Verification Checklist

- [ ] `lk project list` shows `voxie-1` with `*`
- [ ] `cat livekit.toml` shows `subdomain = "voxie-1-f00463v2"`
- [ ] `lk agent create` completes without errors
- [ ] `lk agent status` shows "Running"
- [ ] `lk agent logs` shows agent waiting for rooms
- [ ] Exercise 2 call interface works
- [ ] Agent automatically joins rooms
- [ ] Agent exits when room ends

## Common Issues and Fixes

### Issue: "Cannot find Dockerfile"

**Fix:**
```bash
# Ensure you're in voxie-test directory
cd /Users/muhammad/Personal/Projects/Personal\ Projects/Voxie/voxie/voxie-test
ls -la Dockerfile
# Should exist
```

### Issue: "Authentication failed"

**Fix:**
```bash
# Re-authenticate
lk cloud auth

# Should open browser for login
# After login, verify:
lk project list
```

### Issue: "Agent not joining rooms"

**Fix:**
1. Check agent status: `lk agent status`
2. Check logs: `lk agent logs`
3. Verify environment variables in LiveKit Cloud dashboard
4. Ensure OPENAI_API_KEY is set

### Issue: "Build takes too long"

**Note:** First build can take 5-10 minutes due to:
- Docker image build
- Dependency installation (`uv sync`)
- Upload to LiveKit Cloud

Subsequent deployments (`lk agent deploy`) are faster due to layer caching.

## Alternative: Manual Configuration

If `lk agent create` still fails, you can manually configure:

### Option 1: Delete and Recreate livekit.toml

```bash
# Backup current config
cp livekit.toml livekit.toml.backup

# Delete it
rm livekit.toml

# Run agent create (will generate new config)
lk agent create
```

### Option 2: Use lk agent config

```bash
# Generate new config
lk agent config

# This will prompt for project and create livekit.toml
```

### Option 3: Set Project in Command

```bash
# Specify project explicitly
lk agent create --project voxie-1
```

## Success Indicators

✅ **Deployment Successful** when you see:
```bash
$ lk agent status
✓ Agent Status
  Agent ID: CA_xxxxxxxxx
  Status: Running
  Replicas: 1/1 healthy
  Version: v1
  Last deployment: Just now
```

✅ **Auto-Dispatch Working** when:
- You create a room (via Exercise 2 or API)
- Agent automatically joins (visible in logs)
- Agent handles conversation
- Agent exits when room ends

## Quick Test Script

```bash
#!/bin/bash
# File: test-deployment.sh

echo "🔍 Checking deployment..."

# Check status
echo "📊 Agent Status:"
lk agent status

# Check logs
echo "📝 Recent Logs:"
lk agent logs --tail 20

# Create test room
echo "🧪 Creating test room..."
ROOM_NAME="test-$(date +%s)"
lk token create --room $ROOM_NAME --join

echo "✅ Test complete!"
echo "Watch logs: lk agent logs --follow"
```

Make executable and run:
```bash
chmod +x test-deployment.sh
./test-deployment.sh
```

## Next Steps After Successful Deployment

1. **Set Environment Variables** in LiveKit Cloud dashboard
2. **Test thoroughly** with Exercise 2 interface
3. **Monitor logs** regularly: `lk agent logs`
4. **Set up alerts** in LiveKit Cloud dashboard
5. **Optimize performance** based on usage patterns

## Support

If issues persist:
1. Check full logs: `lk agent logs --tail 100`
2. Verify Docker is running: `docker ps`
3. Check network: Can you access `https://voxie-1-f00463v2.livekit.cloud`?
4. Review: `EXERCISE_3_DEPLOYMENT_GUIDE.md` for detailed troubleshooting

---

## Summary

**Problem**: Empty subdomain in `livekit.toml` caused mismatch error

**Fix**: Updated `subdomain = "voxie-1-f00463v2"` to match your project

**Result**: `lk agent create` should now work successfully

**Test**: Run `lk agent status` and `lk agent logs --follow` to verify
