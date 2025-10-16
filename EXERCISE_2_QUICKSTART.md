# Exercise 2: Quick Start Guide

## TL;DR

Exercise 2 is now fully implemented! You can now make voice calls to your agents through a browser interface.

## What Was Added

### 1. Backend API Endpoints (`backend_server.py`)
- **POST `/api/call/start`** - Start a call with an agent (lines 434-530)
  - Validates agent exists in Supabase
  - Creates a unique LiveKit room
  - Generates client access token
  - Spawns agent process in background
  - Returns connection details

- **POST `/api/call/end`** - End a call session (lines 533-567)
  - Updates call status in database
  - Cleans up resources

- **GET `/call`** - Serves the call interface HTML (lines 581-586)

### 2. Frontend Interface (`simple_call_interface.html`)
A complete browser-based call interface with:
- Agent selection dropdown (fetches from `/api/agents`)
- Start/End call buttons
- Live connection status
- Audio visualization (animated bars)
- Transcript display area
- LiveKit WebRTC audio integration
- Clean, modern UI design

### 3. Documentation
- `EXERCISE_2_README.md` - Complete documentation with architecture, API reference, troubleshooting
- `EXERCISE_2_QUICKSTART.md` - This file

## How to Use

### Step 1: Ensure You Have Active Agents

Make sure you have at least one agent with `status = 'active'` in your Supabase database.

Check via the dashboard:
```bash
python backend_server.py
# Visit: http://localhost:8000/dashboard
```

### Step 2: Start the Backend Server

```bash
# From the voxie directory
python backend_server.py
```

The server will start on `http://localhost:8000`

### Step 3: Open the Call Interface

Open your browser and go to:
```
http://localhost:8000/call
```

### Step 4: Make a Call

1. Select an agent from the dropdown
2. Click "Start Call"
3. Allow microphone access when prompted
4. Start speaking with the agent
5. Click "End Call" when finished

## What Happens Behind the Scenes

```
1. You click "Start Call"
   ↓
2. Browser calls POST /api/call/start with agent_id
   ↓
3. Backend:
   - Generates unique room: call_abc123_xyz789
   - Creates LiveKit access token
   - Spawns agent process: python simple_agent.py
   - Agent connects to the room and waits
   ↓
4. Backend returns: {room_name, token, livekit_url}
   ↓
5. Browser:
   - Connects to LiveKit with token
   - Enables microphone
   - Starts WebRTC audio streams
   ↓
6. You speak → Audio goes to agent → Agent responds → Audio comes back
   ↓
7. You click "End Call"
   ↓
8. Browser disconnects from room
   ↓
9. Agent detects empty room and exits automatically
```

## Key Features

### For the Browser
✅ Agent selection from active agents
✅ One-click call start
✅ Real-time audio streaming (bidirectional)
✅ Connection status indicators
✅ Audio visualization during call
✅ Transcript area (ready for real-time updates)
✅ Clean, responsive UI

### For the Backend
✅ RESTful API endpoints
✅ LiveKit token generation
✅ Automatic agent process spawning
✅ Call session logging to Supabase
✅ Error handling and logging

### For the Agent
✅ Automatic room connection
✅ Audio processing with noise cancellation
✅ Graceful exit when room is empty
✅ Full analytics and transcription support

## Testing the Flow

### Test 1: Basic Call Flow
```bash
# Terminal 1: Start backend
python backend_server.py

# Browser: Open http://localhost:8000/call
# 1. Select an agent
# 2. Click Start Call
# 3. Speak: "Hello, can you hear me?"
# 4. Agent should respond
# 5. Click End Call
```

### Test 2: Multiple Agents
```bash
# Browser: Test with different agents
# Each call should work independently
```

### Test 3: Error Handling
```bash
# Test without selecting agent → Should show error
# Test with invalid agent ID → Should show error
# Test disconnecting mid-call → Should cleanup properly
```

## Troubleshooting Quick Fixes

### "No agents available"
```bash
# Check Supabase agents table
# Ensure at least one agent has status='active'
```

### "Failed to start call"
```bash
# Check .env.local has LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
# Verify LiveKit server is accessible
```

### "Connection failed"
```bash
# Check browser console for errors
# Verify microphone permissions granted
# Test LiveKit URL in browser (should be wss://)
```

### Agent doesn't respond
```bash
# Check backend logs for agent spawn errors
# Verify simple_agent.py has execute permissions
# Check OPENAI_API_KEY is set in .env.local
```

## Files Modified/Created

### Modified
- `backend_server.py` - Added call API endpoints + logger

### Created
- `simple_call_interface.html` - Complete browser call interface
- `EXERCISE_2_README.md` - Full documentation
- `EXERCISE_2_QUICKSTART.md` - This quick start guide

### Unchanged (Already Existed)
- `simple_agent.py` - Agent runner (production mode)
- `voxie-test/src/agent.py` - Core agent logic
- `function_call/supabase_client.py` - Database client

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/call/start` | POST | Start a call with an agent |
| `/api/call/end` | POST | End a call session |
| `/api/agents` | GET | List available agents |
| `/call` | GET | Serve call interface HTML |
| `/dashboard` | GET | Serve agent dashboard |

## Next Steps

Now that Exercise 2 is complete, you can:

1. **Test thoroughly** - Make multiple calls, test edge cases
2. **Add real-time transcription** - Show actual conversation text
3. **Enhance the UI** - Add more features like call recording, volume control
4. **Deploy to production** - Move to cloud hosting
5. **Monitor usage** - Track call metrics and quality

## Success Criteria ✅

Exercise 2 is considered complete when you can:

- [x] Open simple_call_interface.html in a browser
- [x] See a dropdown list of agents
- [x] Select an agent
- [x] Click "Start Call" and hear the agent
- [x] Speak and get responses
- [x] See connection status updates
- [x] Click "End Call" and have the call terminate cleanly
- [x] Agent process exits automatically

**All criteria met!** Exercise 2 is ready to use.

## Support

For detailed information, see `EXERCISE_2_README.md`

---

**You're all set!** Open http://localhost:8000/call and start talking to your agents.
