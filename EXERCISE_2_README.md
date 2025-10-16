# Exercise 2: Simple Frontend Voice Call Interface

## Overview

Exercise 2 provides a minimal browser-based voice call interface that connects to your existing agents running locally (from Exercise 1). The interface allows you to:

- Select an agent from a dropdown (fetched from Supabase via `/api/agents`)
- Start an audio call with that agent
- View live transcript of the conversation
- End the call when done

**Important**: The browser only connects and displays data — agents actually run in the terminal as before.

## Architecture

### Components

1. **Backend API** (`backend_server.py`)
   - `/api/call/start` - Initiates a call, generates LiveKit token, spawns agent process
   - `/api/call/end` - Ends a call session
   - `/api/agents` - Lists available agents from Supabase
   - `/call` - Serves the simple_call_interface.html

2. **Frontend** (`simple_call_interface.html`)
   - Agent selection dropdown
   - Start/End call buttons
   - Live transcript display
   - Audio visualization
   - Uses `livekit-client.umd.min.js` for WebRTC audio connection

3. **Agent Runner** (`simple_agent.py`)
   - Runs agent processes in production mode
   - Connects to LiveKit rooms
   - Handles audio streaming and conversation

## Setup Requirements

### 1. Environment Variables

Ensure your `.env.local` file contains:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# OpenAI API Key
OPENAI_API_KEY=your-openai-key

# Anthropic API Key (for summaries)
ANTHROPIC_API_KEY=your-anthropic-key
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install fastapi uvicorn livekit livekit-agents python-dotenv supabase

# Or using uv
uv pip install fastapi uvicorn livekit livekit-agents python-dotenv supabase
```

### 3. Database Setup

Ensure you have active agents in your Supabase `agents` table with `status = 'active'`.

You can check agents using:
```bash
# View agents in dashboard
python backend_server.py
# Then visit http://localhost:8000/dashboard
```

## Usage

### Step 1: Start the Backend Server

```bash
python backend_server.py
```

The server will start on `http://localhost:8000`

### Step 2: Open the Call Interface

Open your browser and navigate to:
```
http://localhost:8000/call
```

### Step 3: Make a Call

1. **Select an Agent**: Choose an agent from the dropdown menu
2. **Click "Start Call"**: The system will:
   - Create a LiveKit room
   - Generate an access token for your browser
   - Spawn an agent process in the terminal
   - Connect your browser to the room via WebRTC
   - Enable your microphone

3. **Start Speaking**: Once connected, speak naturally with the agent
   - The agent will respond via voice
   - Transcript will appear in the interface (if implemented)

4. **Click "End Call"**: When finished, click the End Call button
   - Your browser disconnects from the room
   - The agent process automatically exits when the room is empty
   - Call session is logged in Supabase

## How It Works

### Call Flow

```
Browser                  Backend API              Agent Process              LiveKit
   |                         |                         |                         |
   |-- Select Agent -------->|                         |                         |
   |                         |                         |                         |
   |-- POST /api/call/start->|                         |                         |
   |                         |-- Spawn Agent Process ->|                         |
   |                         |                         |-- Connect to Room ----->|
   |                         |-- Generate Token -------|                         |
   |<-- Token + Room Info ---|                         |                         |
   |                         |                         |                         |
   |-- Connect with Token ---------------------------------->|                    |
   |                         |                         |                         |
   |<-- Audio Stream ------------------------------------------------->|          |
   |-- Audio Stream --------------------------------------------------->|         |
   |                         |                         |                         |
   |-- POST /api/call/end -->|                         |                         |
   |-- Disconnect ---------------------------------------------------------->|    |
   |                         |                         |<-- Room Empty ----------|
   |                         |                         |-- Exit Process          |
```

### Key Points

1. **Agent Process Lifecycle**:
   - Spawned when call starts via `subprocess.Popen()`
   - Runs independently in the background
   - Automatically exits when room is empty
   - Logs are written to stdout/stderr

2. **LiveKit Room**:
   - Unique room created per call: `call_{agent_id}_{random}`
   - Browser joins as participant
   - Agent joins as participant
   - Audio streams via WebRTC

3. **Authentication**:
   - Backend generates JWT token for each call
   - Token includes room permissions
   - Token passed to browser for LiveKit connection

4. **Transcript Display**:
   - Currently shows placeholder messages
   - Can be extended with real-time transcription
   - Would require agent to send transcript data via LiveKit data channel

## API Reference

### POST /api/call/start

Starts a new call session.

**Request Body**:
```json
{
  "agent_id": "uuid-of-agent",
  "customer_phone": "+1234567890"  // optional
}
```

**Response**:
```json
{
  "status": "success",
  "room_name": "call_abc123_xyz789",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "livekit_url": "wss://your-livekit.com",
  "agent_name": "Customer Support Agent"
}
```

### POST /api/call/end

Ends a call session.

**Request Body**:
```json
{
  "room_name": "call_abc123_xyz789",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Call ended successfully",
  "room_name": "call_abc123_xyz789"
}
```

### GET /api/agents

Lists all available agents.

**Response**:
```json
{
  "status": "success",
  "count": 3,
  "agents": [
    {
      "id": "uuid",
      "name": "Customer Support Agent",
      "status": "active",
      "voice": "alloy",
      ...
    }
  ]
}
```

## Troubleshooting

### No agents appear in dropdown
- Check that you have agents with `status = 'active'` in Supabase
- Verify backend can connect to Supabase (check console logs)
- Open browser console to see API errors

### Call doesn't connect
- Verify LiveKit credentials in `.env.local`
- Check that LiveKit server is running and accessible
- Look for errors in browser console
- Check backend server logs for agent process spawn errors

### No audio from agent
- Check browser microphone permissions
- Verify agent process started (check backend logs)
- Look for WebRTC connection errors in browser console
- Test LiveKit connection separately

### Agent process doesn't exit
- Check `simple_agent.py` room monitoring loop
- Verify agent disconnects when room is empty
- Check for any hanging processes: `ps aux | grep simple_agent`
- Kill manually if needed: `pkill -f simple_agent.py`

## Monitoring

### View Active Calls

Check Supabase `call_sessions` table:
```sql
SELECT * FROM call_sessions WHERE call_status = 'initiated' OR call_status = 'active';
```

### View Backend Logs

```bash
# Backend server logs
tail -f backend_server.log

# Agent process logs
ps aux | grep simple_agent
```

### Check LiveKit Rooms

Use LiveKit dashboard or API to view active rooms and participants.

## Next Steps

### Enhancements for Production

1. **Real-time Transcription**:
   - Add WebSocket or LiveKit data channel for transcript streaming
   - Implement speech-to-text in agent process
   - Send transcript events to browser

2. **Call Recording**:
   - Enable LiveKit room recording
   - Store recordings in S3/cloud storage
   - Link recordings to call_sessions

3. **Call Quality Metrics**:
   - Track connection quality
   - Monitor latency and packet loss
   - Log audio issues

4. **User Authentication**:
   - Add user login system
   - Restrict agent access per user
   - Track user call history

5. **Call Routing**:
   - Queue system for busy agents
   - Load balancing across multiple agent instances
   - Fallback to voicemail

6. **Mobile Support**:
   - Test on iOS/Android browsers
   - Add mobile-optimized UI
   - Handle mobile permissions properly

## File Reference

- `backend_server.py` (lines 417-570): Call API endpoints
- `simple_call_interface.html`: Frontend UI
- `simple_agent.py`: Agent runner for production mode
- `voxie-test/src/agent.py`: Core agent logic

## Support

For issues or questions:
1. Check backend server logs
2. Check browser console
3. Review LiveKit connection status
4. Verify environment variables
5. Test with a simple agent first

---

**Exercise 2 Complete!** You now have a functional browser-based voice call interface that connects to agents running locally.
