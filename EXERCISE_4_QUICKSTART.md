# Exercise 4: Quick Start - Deploy Backend to Railway

## TL;DR - Deploy in 5 Minutes

```bash
# 1. Navigate to project
cd /path/to/voxie

# 2. Install Railway CLI
brew install railway  # or: npm install -g @railway/cli

# 3. Login and deploy
railway login
railway init
railway up

# 4. Set environment variables in Railway dashboard
# (See variables list below)

# 5. Get your URL and test
curl https://voxie-1.railway.app/
```

---

## What's Already Prepared

All deployment files have been created for you:

✅ **`requirements.txt`** - All Python dependencies
✅ **`Procfile`** - Start command for Railway
✅ **`railway.toml`** - Railway configuration
✅ **`.env.example`** - Environment variable template
✅ **`simple_call_interface.html`** - Auto-detects backend URL
✅ **`simple_call_interface_cloud.html`** - Configurable backend URL
✅ **`backend_server.py`** - Already configured for cloud deployment

---

## Step 1: Deploy to Railway (3 minutes)

### Option A: GitHub Deployment (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add backend deployment files for Exercise 4"
   git push origin main
   ```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects Python and deploys

### Option B: CLI Deployment

```bash
cd /path/to/voxie
railway login
railway init
railway up
```

---

## Step 2: Configure Environment Variables (2 minutes)

In Railway dashboard, go to **Variables** tab and add:

```bash
# LiveKit (from Exercise 3)
LIVEKIT_URL=wss://voxie-1-f00463v2.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Supabase
SUPABASE_URL=https://gkfuepzqdzixejspfrlg.supabase.co
SUPABASE_ANON_KEY=your-supabase-key

# OpenAI
OPENAI_API_KEY=sk-proj-your-key

# Optional
RAGIE_API_KEY=your-ragie-key
ANTHROPIC_API_KEY=sk-ant-your-key
DEEPGRAM_API_KEY=your-key
ENABLE_BACKEND_LOGGING=true
```

**Where to find these values:**
- LiveKit: Your `.env` file or LiveKit Cloud dashboard
- Supabase: Your `.env` file or Supabase dashboard
- OpenAI: https://platform.openai.com/api-keys

---

## Step 3: Test Your Deployment (1 minute)

### Test 1: Health Check

```bash
curl https://voxie-1.railway.app/
```

**Expected:**
```json
{
  "status": "ok",
  "service": "voxie-backend",
  "timestamp": "2025-..."
}
```

### Test 2: Load Agents

```bash
curl https://voxie-1.railway.app/api/agents
```

**Expected:**
```json
{
  "status": "success",
  "count": 3,
  "agents": [...]
}
```

---

## Step 4: Test with Frontend

### Method 1: Auto-Detecting Frontend (Easiest)

```bash
cd /path/to/voxie
open simple_call_interface.html
```

- Automatically uses `localhost:8000` when opened locally
- Will use cloud URL when hosted

### Method 2: Cloud-Configured Frontend

```bash
open simple_call_interface_cloud.html
```

1. Enter your Railway URL: `https://voxie-1.railway.app`
2. Click "Load Agents"
3. Select agent
4. Click "Start Call"
5. Speak with your agent!

---

## Troubleshooting

### Problem: "Failed to load agents"

**Fix:**
1. Check Railway logs: Railway Dashboard → Logs
2. Verify Supabase environment variables are set
3. Test: `curl https://voxie-1.railway.app/api/agents`

### Problem: "Failed to start call"

**Fix:**
1. Verify LiveKit environment variables are set
2. Check that Exercise 3 agent is deployed:
   ```bash
   cd voxie-test
   lk agent status
   ```

### Problem: Backend crash on startup

**Fix:**
1. Check Railway build logs
2. Verify all required environment variables are set
3. Test locally:
   ```bash
   pip install -r requirements.txt
   python backend_server.py
   ```

---

## Quick Command Reference

```bash
# Railway CLI
railway login              # Login to Railway
railway init               # Initialize project
railway up                 # Deploy
railway logs               # View logs
railway status             # Check deployment status

# Testing
curl https://voxie-1.railway.app/              # Health check
curl https://voxie-1.railway.app/api/agents    # List agents

# Updating
git push origin main       # Auto-redeploys on Railway
railway up                 # Or redeploy via CLI
```

---

## Success Checklist

Exercise 4 is complete when:

- [ ] Backend deployed to Railway
- [ ] Health endpoint returns `{"status": "ok"}`
- [ ] `/api/agents` returns agents from Supabase
- [ ] Frontend loads agents from cloud backend
- [ ] "Start Call" works end-to-end
- [ ] Agent joins and responds
- [ ] "End Call" disconnects properly

---

## Architecture (What You Just Deployed)

```
Browser (simple_call_interface.html)
    ↓
Railway Backend (FastAPI)
    ↓                     ↓
Supabase DB      LiveKit Cloud
                       ↓
                 Cloud Agent (Exercise 3)
```

**Flow:**
1. User clicks "Start Call"
2. Browser → Railway: Create room
3. Railway → LiveKit: Generate token
4. Browser ↔ LiveKit ↔ Agent: Voice conversation
5. User clicks "End Call"

---

## Next Steps

1. **Share your frontend** - Anyone can use it with your cloud backend
2. **Monitor costs** - Check Railway dashboard
3. **Set up custom domain** - Railway Settings → Domains
4. **Add error monitoring** - Sentry, Rollbar
5. **Build mobile app** - Call your backend APIs

---

## Need Full Details?

See **`EXERCISE_4_BACKEND_DEPLOYMENT.md`** for:
- Complete deployment guides for Railway, Render, Fly.io
- Detailed troubleshooting
- Environment variable reference
- Architecture diagrams
- Cost breakdown

---

**You're Done!** 🎉

Your backend is now live at `https://voxie-1.railway.app` and accessible from anywhere.
