# Exercise 4: Deploy Backend to Railway/Render/Fly.io

## Overview

This guide walks you through deploying the Voxie FastAPI backend to Railway (recommended), Render, or Fly.io, completing Exercise 4 of the Voxie onboarding.

**What we're deploying:**
- FastAPI backend server (`backend_server.py`)
- Agent CRUD APIs
- Call management endpoints (Exercise 2)
- Analytics APIs
- Supporting Python modules

**What you'll get:**
- Public API URL: `https://voxie-1.railway.app`
- Backend accessible from any frontend (local or hosted)
- Cloud-based call management system

---

## Prerequisites

✅ Completed Exercise 3 (Agent deployed to LiveKit Cloud)
✅ Have the following API keys ready:
- LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
- SUPABASE_URL, SUPABASE_ANON_KEY
- OPENAI_API_KEY
- RAGIE_API_KEY (optional)
- ANTHROPIC_API_KEY (optional)
- DEEPGRAM_API_KEY (optional)

---

## Files Required for Deployment

The following files in the root `/voxie` directory are required:

### Core Backend Files:
```
voxie/
├── backend_server.py              # Main FastAPI server
├── requirements.txt               # Python dependencies (created)
├── Procfile                       # Start command for Railway (created)
├── railway.toml                   # Railway configuration (created)
├── .env.example                   # Environment variable template (created)
├── simple_agent.py                # Agent runner
├── function_call/
│   ├── supabase_client.py        # Database client
│   ├── agent_persistence.py      # Agent data handler
│   └── (other modules)
├── voxie-test/
│   └── src/
│       ├── agent.py              # Main agent logic
│       └── (other modules)
├── simple_call_interface.html     # Frontend (auto-detects backend URL)
├── simple_call_interface_cloud.html  # Frontend with configurable backend URL
└── agent_dashboard.html           # Agent management UI
```

### Deployment Configuration Files (Already Created):

**`requirements.txt`**
- Contains all Python dependencies
- Includes FastAPI, LiveKit, Supabase, OpenAI, etc.

**`Procfile`**
- Tells Railway how to start the server
- Contains: `web: uvicorn backend_server:app --host 0.0.0.0 --port $PORT`

**`railway.toml`**
- Railway-specific configuration
- Defines health checks and restart policies

**`.env.example`**
- Template for environment variables
- Copy this to configure your deployment

---

## Deployment Option 1: Railway (Recommended)

Railway is the easiest option with excellent Python support and automatic deployments.

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Create a new project

### Step 2: Deploy from GitHub

**Option A: Deploy from GitHub (Recommended)**

1. Push your code to GitHub:
   ```bash
   cd /path/to/voxie
   git add .
   git commit -m "Add backend deployment files"
   git push origin main
   ```

2. In Railway dashboard:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the Python project

**Option B: Deploy from Local**

1. Install Railway CLI:
   ```bash
   # macOS
   brew install railway

   # Or using npm
   npm install -g @railway/cli
   ```

2. Login and deploy:
   ```bash
   cd /path/to/voxie
   railway login
   railway init
   railway up
   ```

### Step 3: Configure Environment Variables

In Railway dashboard:

1. Go to your project
2. Click on "Variables" tab
3. Add the following environment variables:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://voxie-1-f00463v2.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Supabase Configuration
SUPABASE_URL=https://gkfuepzqdzixejspfrlg.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# API Keys
OPENAI_API_KEY=sk-proj-your-openai-key
RAGIE_API_KEY=your-ragie-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
DEEPGRAM_API_KEY=your-deepgram-key

# Backend Configuration
ENABLE_BACKEND_LOGGING=true
```

**Note:** Railway automatically provides `PORT` environment variable, so you don't need to set it.

### Step 4: Deploy

Railway will automatically deploy when you:
- Push to GitHub (if using GitHub deployment)
- Run `railway up` (if using CLI)

**Deployment Process:**
1. Railway builds your project
2. Installs dependencies from `requirements.txt`
3. Runs the start command from `Procfile`
4. Exposes your app on a public URL

### Step 5: Get Your Backend URL

Your deployment URL is:
```
https://voxie-1.railway.app
```

This is your permanent backend API URL!

---

## Deployment Option 2: Render

### Step 1: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Create New Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name:** voxie-backend
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend_server:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Environment Variables

In Render dashboard, go to "Environment" tab and add all variables listed above.

### Step 4: Deploy

Click "Create Web Service" - Render will deploy your app.

---

## Deployment Option 3: Fly.io

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

### Step 2: Login and Initialize

```bash
cd /path/to/voxie
fly auth login
fly launch
```

Follow the prompts:
- App name: `voxie-backend`
- Region: Choose closest to you
- Database: Skip (using Supabase)

### Step 3: Configure Secrets

```bash
fly secrets set LIVEKIT_URL=wss://voxie-1-f00463v2.livekit.cloud
fly secrets set LIVEKIT_API_KEY=your-key
fly secrets set LIVEKIT_API_SECRET=your-secret
fly secrets set SUPABASE_URL=https://your-project.supabase.co
fly secrets set SUPABASE_ANON_KEY=your-key
fly secrets set OPENAI_API_KEY=sk-proj-your-key
```

### Step 4: Deploy

```bash
fly deploy
```

---

## Testing Your Deployment

### 1. Test Health Endpoint

```bash
curl https://voxie-1.railway.app/
```

**Expected response:**
```json
{
  "status": "ok",
  "service": "voxie-backend",
  "timestamp": "2025-10-17T..."
}
```

### 2. Test Agents API

```bash
curl https://voxie-1.railway.app/api/agents
```

**Expected response:**
```json
{
  "status": "success",
  "count": 3,
  "agents": [...]
}
```

### 3. Test with Frontend

**Option A: Use Auto-Detecting Frontend**

1. Open `simple_call_interface.html` locally:
   ```bash
   open simple_call_interface.html
   ```

2. The frontend will automatically use `http://localhost:8000` when opened locally

**Option B: Use Cloud-Configured Frontend**

1. Open `simple_call_interface_cloud.html` locally:
   ```bash
   open simple_call_interface_cloud.html
   ```

2. Enter your backend URL: `https://voxie-1.railway.app`

3. Click "Load Agents"

4. Select an agent and click "Start Call"

5. Speak with your cloud-deployed agent!

---

## Verifying End-to-End Flow

### Expected Behavior:

1. **Frontend → Backend:**
   - User clicks "Start Call" in browser
   - Browser calls `POST /api/call/start` on Railway backend
   - Backend returns LiveKit room name and token

2. **Backend → LiveKit:**
   - Backend creates LiveKit room
   - Backend spawns agent process (or triggers cloud agent)

3. **LiveKit Cloud Agent → Room:**
   - Cloud agent (from Exercise 3) auto-joins the room
   - Agent starts listening and responding

4. **Browser → LiveKit → Agent:**
   - Browser connects to LiveKit room with WebRTC
   - User speaks → Agent responds via LiveKit
   - Transcripts flow in real-time

### Success Indicators:

✅ Health endpoint returns `{"status": "ok"}`
✅ `/api/agents` returns list of agents from Supabase
✅ Browser can load agents from cloud backend
✅ "Start Call" successfully creates a room
✅ Agent joins and responds to voice input
✅ Transcripts appear in real-time
✅ "End Call" properly disconnects

---

## Checking Logs

### Railway Logs:
```bash
# In Railway dashboard, click "Logs" tab
# Or using CLI:
railway logs
```

**Look for:**
```
✅ Loaded environment from .env
🚀 Starting agent {agent_id} for room {room_name}
✅ Agent process started for room: call_...
```

### Common Log Messages:

**Success:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Backend server starting...
```

**Agent Call Started:**
```
🚀 Starting agent 066abbac-... for room call_066abbac_abc123
✅ Agent process started for room: call_066abbac_abc123
```

**Error - Missing Environment Variable:**
```
ValueError: SUPABASE_URL and SUPABASE_ANON_KEY must be set
```
**Fix:** Add missing environment variable in Railway dashboard

---

## Troubleshooting

### Issue 1: "Failed to load agents"

**Cause:** Backend can't connect to Supabase

**Fix:**
1. Check Railway logs for error messages
2. Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
3. Test Supabase connection:
   ```bash
   curl https://your-project.supabase.co/rest/v1/
   ```

### Issue 2: "Failed to start call"

**Cause:** Missing LiveKit credentials or agent not found

**Fix:**
1. Verify LiveKit environment variables are set:
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
2. Check that agents exist in Supabase `agents` table
3. Check Railway logs for detailed error

### Issue 3: "Agent not joining room"

**Cause:**
- Cloud agent (Exercise 3) not deployed to LiveKit
- Agent spawn failing in backend

**Fix:**
1. Verify Exercise 3 agent is deployed:
   ```bash
   cd voxie-test
   lk agent status
   ```
2. Check LiveKit Cloud agent logs:
   ```bash
   lk agent logs
   ```
3. Ensure `simple_agent.py` exists in backend deployment

### Issue 4: "CORS Error" in Browser

**Cause:** Frontend domain not allowed by backend CORS settings

**Fix:**
Backend already has `allow_origins=["*"]` in `backend_server.py:84`

If you want to restrict to specific domains:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    ...
)
```

### Issue 5: Backend Crashes on Startup

**Cause:** Missing Python dependencies or import errors

**Fix:**
1. Check Railway build logs for import errors
2. Verify all dependencies in `requirements.txt`
3. Test locally:
   ```bash
   cd voxie
   pip install -r requirements.txt
   python backend_server.py
   ```

---

## Updating Your Deployment

### Method 1: Git Push (Recommended)

```bash
cd voxie
git add .
git commit -m "Update backend"
git push origin main
```

Railway will automatically redeploy.

### Method 2: Railway CLI

```bash
cd voxie
railway up
```

### Method 3: Railway Dashboard

1. Go to Railway dashboard
2. Click "Deployments"
3. Click "Redeploy"

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      User's Browser                          │
│  (simple_call_interface.html or simple_call_interface_cloud.html)  │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 │ HTTP/HTTPS
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                Railway Backend Server                        │
│              (backend_server.py - FastAPI)                   │
│                                                              │
│  Endpoints:                                                  │
│  • GET  /                    (health check)                 │
│  • GET  /api/agents          (list agents)                  │
│  • POST /api/call/start      (create room + token)          │
│  • POST /api/call/end        (end call)                     │
│  • GET  /api/analytics/*     (analytics data)               │
└────────────┬───────────────────┬─────────────────────────────┘
             │                   │
             │                   │
             ▼                   ▼
┌─────────────────────┐  ┌──────────────────────────────────┐
│   Supabase DB       │  │     LiveKit Cloud                │
│   (agents, calls)   │  │  (voice communication)           │
└─────────────────────┘  └──────────┬───────────────────────┘
                                    │
                                    │ Auto-dispatch
                                    ▼
                         ┌──────────────────────────┐
                         │   Cloud Agent            │
                         │   (Exercise 3)           │
                         │   Runs on LiveKit Cloud  │
                         └──────────────────────────┘
```

**Request Flow:**

1. **User clicks "Start Call"**
   - Frontend → Railway Backend: `POST /api/call/start`

2. **Backend creates room**
   - Backend → Supabase: Fetch agent config
   - Backend → LiveKit: Create room, generate token
   - Backend → Frontend: Return room name + token

3. **Frontend connects to LiveKit**
   - Frontend → LiveKit Cloud: Connect via WebRTC
   - Frontend: Enable microphone

4. **Cloud agent joins automatically**
   - LiveKit Cloud → Agent: Auto-dispatch to room
   - Agent joins and starts listening

5. **Voice conversation**
   - User speaks → LiveKit → Agent (via OpenAI Realtime API)
   - Agent responds → LiveKit → User
   - Transcripts flow bidirectionally

6. **User clicks "End Call"**
   - Frontend → Railway Backend: `POST /api/call/end`
   - Frontend → LiveKit: Disconnect
   - Agent: Detects empty room, exits

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `LIVEKIT_URL` | ✅ | LiveKit Cloud WebSocket URL | `wss://voxie-1-f00463v2.livekit.cloud` |
| `LIVEKIT_API_KEY` | ✅ | LiveKit API key | `APIWuHiyFH89Kfq` |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit API secret | `fJdLQd...` |
| `SUPABASE_URL` | ✅ | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key | `eyJhbGc...` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for agents | `sk-proj-...` |
| `RAGIE_API_KEY` | ⚠️ | Ragie API key (if using RAG) | `tnt_...` |
| `ANTHROPIC_API_KEY` | ⚠️ | Anthropic API key (if using Claude) | `sk-ant-...` |
| `DEEPGRAM_API_KEY` | ⚠️ | Deepgram API key (if using STT) | `your-key` |
| `ENABLE_BACKEND_LOGGING` | ❌ | Enable verbose logging | `true` |

---

## Cost Considerations

### Railway:
- **Free Tier:** $5/month credits (500 hours)
- **Starter Plan:** $5/month + usage
- **Pro Plan:** $20/month + usage

**Typical backend costs:** ~$5-10/month for low-medium traffic

### LiveKit Cloud (from Exercise 3):
- Pay per usage (agent runtime, bandwidth)
- See LiveKit dashboard for real-time costs

### Supabase:
- **Free Tier:** 500MB database, 2GB bandwidth
- **Pro:** $25/month

---

## Next Steps After Deployment

1. **✅ Test thoroughly** with multiple calls
2. **✅ Monitor costs** in Railway dashboard
3. **✅ Set up custom domain** (optional):
   - Railway: Settings → Domains
4. **✅ Enable HTTPS** (automatic with Railway)
5. **✅ Set up error monitoring** (Sentry, Rollbar)
6. **✅ Configure auto-scaling** if needed
7. **✅ Set up CI/CD** for automatic deployments

---

## Success Criteria for Exercise 4

Exercise 4 is complete when:

✅ Backend deployed to Railway/Render/Fly.io
✅ Public API URL accessible (e.g., `https://voxie-1.railway.app`)
✅ Health endpoint returns `{"status": "ok"}`
✅ `/api/agents` returns agents from Supabase
✅ Frontend (local or hosted) can connect to cloud backend
✅ "Start Call" creates a room and agent joins
✅ Voice conversation works end-to-end
✅ "End Call" properly disconnects
✅ Backend logs show no errors

---

## Summary

**What you deployed:**
- FastAPI backend server
- Agent management APIs
- Call orchestration system

**What it does:**
- Serves frontend applications
- Creates LiveKit rooms
- Manages agent lifecycle
- Provides analytics data

**How it works:**
- Frontend calls backend API
- Backend creates LiveKit room + token
- Cloud agent (Exercise 3) auto-joins
- User speaks with agent via WebRTC

**You're done!** 🎉

Your backend is now live and accessible from anywhere. You can:
- Share the frontend HTML file with anyone
- Build mobile apps that call your backend
- Integrate voice calls into other applications

---

## Need Help?

1. **Check Railway logs:** Railway Dashboard → Logs
2. **Check LiveKit agent logs:** `lk agent logs`
3. **Review error messages** in browser console (F12)
4. **Verify environment variables** are set correctly
5. **Test each component** individually (health, agents, call start)

**Common Issues:**
- Missing environment variables → Add in Railway dashboard
- CORS errors → Check `backend_server.py` CORS settings
- Agent not joining → Verify Exercise 3 agent is deployed

---

**Exercise 4 Complete!** Your Voxie backend is now deployed and accessible from anywhere. 🚀
