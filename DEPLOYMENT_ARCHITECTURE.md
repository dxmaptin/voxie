# Voxie Deployment Architecture Guide

This guide explains how the Voxie system components interact and how to deploy them to production.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Static HTML)                      │
│  • frontend_demo.html - SSE log viewer (optional monitoring)     │
│  • Direct LiveKit SDK integration for voice calls               │
└─────────────────────────────────────────────────────────────────┘
         │                                              │
         │ (SSE logs only)                             │ (Voice/Audio)
         ▼                                              ▼
┌───────────────────────┐                  ┌────────────────────────┐
│   BACKEND API         │                  │  LIVEKIT CLOUD         │
│   (FastAPI Server)    │                  │  (Voice Infrastructure)│
│                       │                  │                        │
│ • Agent CRUD          │                  │ • WebRTC Rooms         │
│ • Analytics API       │                  │ • Audio Streaming      │
│ • SSE Log Stream      │                  │ • Participant Mgmt     │
│ • Dashboard HTML      │                  └────────────────────────┘
└───────────────────────┘                             │
         │                                              │
         │ (Database queries)                          │ (Joins room)
         ▼                                              ▼
┌───────────────────────┐                  ┌────────────────────────┐
│   SUPABASE DATABASE   │                  │  VOXIE AGENTS          │
│   (PostgreSQL)        │                  │  (Python Processes)    │
│                       │◄─────────────────│                        │
│ • agents              │  (Saves data)    │ • Voxie (creator)      │
│ • call_sessions       │                  │ • Sub-agents           │
│ • call_summaries      │                  │ • Analytics tracking   │
│ • token_usage         │                  │ • Call transcription   │
└───────────────────────┘                  └────────────────────────┘
```

## 🔍 Component Interactions

### 1. Frontend → Backend (HTTP/SSE)

**What frontend does:**
- Makes HTTP REST calls to backend API
- Opens SSE connection to stream real-time logs
- **Does NOT** handle voice calls through backend

**Backend endpoints used:**
```javascript
// In frontend_demo.html (line 289, 367)
const backendUrl = 'http://localhost:8000';
const url = `${backendUrl}/api/agents/create-stream/${currentSessionId}`;
```

**Data flow:**
```
Frontend (HTML/JS) → HTTP GET → Backend API
                  ← SSE Stream ← (real-time logs)
```

### 2. Frontend → LiveKit (WebRTC)

**For voice interactions, frontend must:**
- Import LiveKit JavaScript SDK
- Connect directly to LiveKit rooms
- Handle WebRTC audio streams

**Example integration (NOT currently in your frontend):**
```html
<!-- Add to HTML -->
<script src="https://unpkg.com/livekit-client/dist/livekit-client.umd.min.js"></script>

<script>
  // Connect to LiveKit room for voice
  const room = new LiveKitClient.Room();
  await room.connect('wss://demo-z16kr3dd.livekit.cloud', token);

  // Enable microphone
  await room.localParticipant.setMicrophoneEnabled(true);
</script>
```

**Data flow:**
```
User microphone → Frontend (LiveKit SDK) → LiveKit Cloud (WebRTC)
                                         ↓
                                  Voxie Agent (in room)
                                         ↓
                                  OpenAI Realtime API
                                         ↓
                                  Audio response → User speakers
```

### 3. Backend → Supabase (Database)

**Backend queries database for:**
- Listing agents (`GET /api/agents`)
- Agent details (`GET /api/agents/{id}`)
- Analytics data (`GET /api/analytics/summary`)
- Call history (`GET /api/analytics/recent-calls`)

**Data flow:**
```
Backend API → Supabase REST API → PostgreSQL Database
           ← JSON response ←
```

### 4. Voxie Agents → LiveKit Cloud (Voice)

**Agents connect to LiveKit for:**
- Real-time voice communication
- Audio transcription (via Deepgram)
- Speaking responses (via OpenAI Realtime)

**Data flow:**
```
Voxie Agent → LiveKit Cloud (wss://demo-z16kr3dd.livekit.cloud)
           ← Audio streams ←
           → Audio responses →
```

### 5. Voxie Agents → Supabase (Database)

**Agents save to database:**
- Agent configurations (when created)
- Call sessions (start/end times)
- Conversation turns (transcripts)
- Call summaries (GPT-4o generated)
- Token usage (costs)

**Data flow:**
```
Voxie Agent → Supabase Client → PostgreSQL
           ← Confirmation ←
```

## 📊 Current Frontend Capabilities

### ✅ What `frontend_demo.html` DOES:

1. **Connects to backend SSE stream** (line 367-368)
   ```javascript
   const url = `${backendUrl}/api/agents/create-stream/${currentSessionId}`;
   eventSource = new EventSource(url);
   ```

2. **Displays real-time logs** during agent creation
   - Connection status
   - Processing steps
   - Completion messages
   - Error notifications

3. **Visual monitoring only** - does NOT handle:
   - Voice calls
   - Audio streaming
   - LiveKit connections
   - Agent activation

### ❌ What `frontend_demo.html` DOES NOT DO:

1. **Does NOT connect to LiveKit** for voice
   - No LiveKit SDK imported
   - No room connection code
   - No audio handling

2. **Does NOT start voice calls** with agents
   - We removed `/api/call/start` endpoint
   - No agent spawning from frontend
   - No LiveKit token generation

3. **Does NOT interact with Voxie** via voice
   - Users must use LiveKit rooms directly
   - Can't talk to Voxie from this frontend

## 🚀 Deployment Scenarios

### Scenario A: Backend + Frontend on Same Server

```yaml
Deployment:
  - Backend API: https://your-domain.com (FastAPI on port 8000)
  - Frontend: https://your-domain.com/frontend_demo.html (static file)
  - Database: Supabase Cloud (separate)
  - LiveKit: LiveKit Cloud (separate)
  - Voxie Agents: Separate compute instances

User workflow:
  1. Visit https://your-domain.com/frontend_demo.html
  2. See agent creation logs in real-time (monitoring only)
  3. Connect to Voxie via separate LiveKit client/app
```

**Environment variables needed:**
```bash
# Backend .env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
LIVEKIT_URL=wss://demo-z16kr3dd.livekit.cloud
LIVEKIT_API_KEY=APIULtFuk4ed8Ma
LIVEKIT_API_SECRET=xxx
OPENAI_API_KEY=sk-proj-xxx
ENABLE_BACKEND_LOGGING=true
BACKEND_URL=https://your-domain.com
```

### Scenario B: Backend and Frontend Separately Deployed

```yaml
Deployment:
  - Backend API: https://api.your-domain.com (FastAPI)
  - Frontend: https://app.your-domain.com (Static hosting)
  - Database: Supabase Cloud
  - LiveKit: LiveKit Cloud
  - Voxie Agents: Separate compute instances

Frontend config:
  - Update line 289 in frontend_demo.html:
    const backendUrl = 'https://api.your-domain.com';
```

### Scenario C: Full Voice-Enabled Frontend (Recommended)

To create a complete voice-enabled frontend:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voxie Voice Interface</title>
    <!-- Import LiveKit SDK -->
    <script src="https://unpkg.com/livekit-client/dist/livekit-client.umd.min.js"></script>
</head>
<body>
    <button id="connectBtn">Connect to Voxie</button>
    <div id="status">Disconnected</div>

    <script>
        const backendUrl = 'https://api.your-domain.com';
        const livekitUrl = 'wss://demo-z16kr3dd.livekit.cloud';

        async function connectToVoxie() {
            // Step 1: Create a LiveKit room (you'd do this via your backend or LiveKit dashboard)
            const roomName = 'voxie-room-' + Date.now();

            // Step 2: Generate access token (should come from your backend)
            // For now, using LiveKit API directly
            const token = await generateLiveKitToken(roomName);

            // Step 3: Connect to room
            const room = new LiveKitClient.Room();
            await room.connect(livekitUrl, token);

            // Step 4: Enable microphone
            await room.localParticipant.setMicrophoneEnabled(true);

            document.getElementById('status').textContent = 'Connected to Voxie';

            // Step 5: Listen for Voxie's audio
            room.on('trackSubscribed', (track, publication, participant) => {
                if (track.kind === 'audio') {
                    const audioElement = track.attach();
                    document.body.appendChild(audioElement);
                }
            });
        }

        document.getElementById('connectBtn').onclick = connectToVoxie;
    </script>
</body>
</html>
```

## 🔑 Key Deployment Questions Answered

### Q1: Does frontend use ONLY LiveKit?

**Answer:** No, your current frontend (`frontend_demo.html`) uses:
- ✅ Backend API (via HTTP/SSE) for logs and monitoring
- ❌ Does NOT use LiveKit at all (no SDK imported)

For voice interaction, you need to add LiveKit SDK to frontend.

### Q2: Does frontend need both Backend AND LiveKit?

**Answer:** Depends on functionality:

| Feature | Backend API | LiveKit Cloud |
|---------|------------|---------------|
| View agent list | ✅ Required | ❌ Not needed |
| See analytics | ✅ Required | ❌ Not needed |
| Real-time logs | ✅ Required (SSE) | ❌ Not needed |
| Voice calls with Voxie | ❌ Not needed | ✅ Required |
| Audio streaming | ❌ Not needed | ✅ Required |

**Current setup:** Frontend only uses Backend API (no voice capability)

**Recommended setup:** Frontend uses BOTH:
- Backend API for data/analytics
- LiveKit Cloud for voice calls

### Q3: Can frontend work if backend is down but LiveKit is up?

**Answer:** Partially:
- ❌ Can't see agent list or analytics (needs backend)
- ❌ Can't see real-time logs (needs backend SSE)
- ✅ Can still make voice calls to Voxie (only needs LiveKit)

### Q4: Where should I deploy what?

**Recommended:**

```
┌─────────────────────────────────────────────────────────────┐
│ STATIC FILE HOSTING (Vercel, Netlify, S3)                  │
│ • frontend_demo.html                                        │
│ • Any HTML/CSS/JS files                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ BACKEND API SERVER (Railway, Render, Fly.io, AWS)          │
│ • backend_server.py (FastAPI)                               │
│ • requirements-backend.txt                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ VOXIE AGENTS (Dedicated compute, AWS EC2, GCP)              │
│ • voxie-test/src/agent.py                                   │
│ • Run in dev mode: python src/agent.py dev                  │
│ • Auto-joins any LiveKit rooms                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MANAGED SERVICES (Cloud providers)                          │
│ • Supabase: Database (already cloud-hosted)                 │
│ • LiveKit Cloud: Voice infrastructure (already hosted)      │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Deployment Checklist

### 1. Deploy Backend API

```bash
# Platform: Railway, Render, Fly.io
# Files needed:
- backend_server.py
- requirements-backend.txt
- .env (with all credentials)

# Set environment variables in platform:
SUPABASE_URL=xxx
SUPABASE_ANON_KEY=xxx
LIVEKIT_URL=wss://demo-z16kr3dd.livekit.cloud
LIVEKIT_API_KEY=APIULtFuk4ed8Ma
LIVEKIT_API_SECRET=xxx
OPENAI_API_KEY=xxx
ENABLE_BACKEND_LOGGING=true

# Command to run:
python backend_server.py
```

### 2. Deploy Frontend

```bash
# Platform: Vercel, Netlify, S3, or same server as backend
# Files needed:
- frontend_demo.html

# Update line 289 with your backend URL:
const backendUrl = 'https://your-api-domain.com';

# Deploy as static file
```

### 3. Deploy Voxie Agents

```bash
# Platform: AWS EC2, GCP Compute, or any VPS
# Files needed:
- voxie-test/src/agent.py
- All dependencies from requirements.txt
- .env.local with credentials

# Run command:
cd voxie-test
uv run python src/agent.py dev

# This keeps Voxie running 24/7, auto-joining new rooms
```

### 4. Test End-to-End

```bash
# 1. Test Backend API
curl https://your-api-domain.com/api/agents

# 2. Test Frontend (open in browser)
https://your-frontend-domain.com/frontend_demo.html

# 3. Test Voxie Agent (create LiveKit room and join)
# Use LiveKit Playground or custom client

# 4. Verify logs appear in frontend
# Enter session ID and see real-time logs streaming
```

## 📝 Summary

**Your current architecture:**
- ✅ Backend API is deployed → serves agent data & analytics
- ✅ LiveKit Cloud is configured → handles voice infrastructure
- ✅ Frontend can view logs → connects to backend via SSE
- ❌ Frontend CANNOT make voice calls → no LiveKit SDK

**To enable full voice functionality:**
1. Add LiveKit SDK to your frontend
2. Create room join flow in frontend
3. Connect frontend to LiveKit Cloud
4. Keep backend for data/analytics only

**Deployment summary:**
- Frontend: Static hosting (Vercel/Netlify)
- Backend: API server (Railway/Render)
- Voxie Agents: Long-running compute (EC2/VPS)
- Database: Supabase Cloud (already hosted)
- Voice: LiveKit Cloud (already hosted)
