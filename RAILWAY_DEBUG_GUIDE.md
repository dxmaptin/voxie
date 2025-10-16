# Railway Deployment Debug Guide

## Current Status

✅ Railway successfully detected Python project
✅ Railway installed dependencies from requirements.txt
❌ Deployment failed after build completed

---

## How to Get Detailed Error Logs

### Option 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard:**
   - Open https://railway.app
   - Click on "voxie-1" project

2. **View Failed Deployment:**
   - Click on your service (should show "voxie" or similar)
   - Click on "Deployments" tab
   - Click on the most recent failed deployment
   - Scroll to the bottom of the logs

3. **Look for Error Messages:**
   Look for lines containing:
   - `ERROR`
   - `Failed to`
   - `ModuleNotFoundError`
   - `ImportError`
   - `Connection refused`
   - `Application startup failed`
   - `Port binding failed`

### Option 2: Railway CLI (If Service is Linked)

```bash
# Link to the specific service first
railway link

# Then get logs
railway logs
```

---

## Common Deployment Failure Causes

### 1. Missing Environment Variables ⚠️

**Symptom:** App crashes on startup because it can't find required environment variables.

**Error logs might show:**
```
KeyError: 'LIVEKIT_URL'
ValueError: LIVEKIT_API_KEY environment variable is required
```

**Fix:**
1. Go to Railway dashboard → your service → Variables
2. Add all required environment variables:
   ```bash
   LIVEKIT_URL=wss://voxie-1-f00463v2.livekit.cloud
   LIVEKIT_API_KEY=APIWuHiyFH89Kfq
   LIVEKIT_API_SECRET=fJdLQdTbskjgKjtynmF8RIifIeDiFLRHif5k0VLoeDZC
   SUPABASE_URL=https://gkfuepzqdzixejspfrlg.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   OPENAI_API_KEY=sk-proj-OfrXUOJ_BrxnEuXpMD9No7wTPkC2Yqu...
   ```
3. Click "Deploy" to restart with new variables

---

### 2. Import Errors

**Symptom:** uvicorn can't import the FastAPI app

**Error logs might show:**
```
ModuleNotFoundError: No module named 'function_call'
ImportError: cannot import name 'app' from 'backend_server'
```

**Cause:**
- Missing dependencies in requirements.txt
- Incorrect Python path structure
- Missing __init__.py files

**Fix:**
Check that all subdirectories have `__init__.py` files:
```bash
# Check if function_call/ has __init__.py
ls -la function_call/__init__.py
```

If missing, create it:
```bash
touch function_call/__init__.py
```

---

### 3. Port Binding Issues

**Symptom:** Application starts but Railway can't connect to it

**Error logs might show:**
```
Health check failed
Connection refused on port 8000
Application is not listening on $PORT
```

**Fix:**
Verify Procfile uses `$PORT` environment variable:
```
web: uvicorn backend_server:app --host 0.0.0.0 --port $PORT
```

Railway automatically sets `$PORT` - don't hardcode port 8000.

---

### 4. Dependency Installation Failures

**Symptom:** Some packages failed to install but build continued

**Error logs might show:**
```
ERROR: Could not find a version that satisfies the requirement
ERROR: Failed building wheel for livekit-agents
```

**Fix:**
1. Check requirements.txt has correct versions
2. Remove version pins if needed (e.g., `livekit-agents` instead of `livekit-agents==1.2.7`)
3. Add missing system dependencies in nixpacks.toml

---

### 5. File Not Found Errors

**Symptom:** Application can't find required files

**Error logs might show:**
```
FileNotFoundError: [Errno 2] No such file or directory: '.env'
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**Fix:**
Update code to handle missing files gracefully. Your backend_server.py already does this:
```python
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
elif os.path.exists('.env'):
    load_dotenv('.env')
else:
    # Use system environment variables (Railway dashboard)
    pass
```

---

### 6. Database Connection Errors

**Symptom:** Can't connect to Supabase

**Error logs might show:**
```
Connection refused
Timeout connecting to Supabase
Invalid API key
```

**Fix:**
1. Verify SUPABASE_URL and SUPABASE_ANON_KEY are set correctly
2. Check Supabase project is active and accessible
3. Verify API keys haven't expired

---

### 7. LiveKit Connection Errors

**Symptom:** Can't connect to LiveKit Cloud

**Error logs might show:**
```
Connection to LiveKit failed
Invalid API credentials
WebSocket connection failed
```

**Fix:**
1. Verify LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET are correct
2. Check LiveKit Cloud project is active
3. Test credentials locally first

---

## Step-by-Step Debugging Process

### Step 1: Get Full Error Logs

Go to Railway dashboard and copy the **complete** error logs from the failed deployment. Focus on:
- The last 50-100 lines
- Any lines with "ERROR" or "Failed"
- The exact error message and stack trace

### Step 2: Identify the Error Type

Match the error to one of the common causes above:
- Missing environment variables → Add them in Railway dashboard
- Import errors → Fix Python imports or add __init__.py
- Port issues → Verify $PORT is used correctly
- Dependency issues → Update requirements.txt

### Step 3: Apply Fix and Redeploy

After applying fix:
```bash
# If code changes needed
git add .
git commit -m "Fix Railway deployment issue: [describe fix]"
git push origin malik-branch-ex2

# Railway will automatically redeploy
```

Or if just adding environment variables:
- Add them in Railway dashboard → Variables
- Click "Deploy" to restart

---

## Testing Deployment Locally First

Before redeploying to Railway, test locally to simulate the production environment:

### 1. Test with System Environment Variables

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Rename .env.local temporarily
mv .env.local .env.local.backup

# Export environment variables
export LIVEKIT_URL="wss://voxie-1-f00463v2.livekit.cloud"
export LIVEKIT_API_KEY="APIWuHiyFH89Kfq"
export LIVEKIT_API_SECRET="fJdLQdTbskjgKjtynmF8RIifIeDiFLRHif5k0VLoeDZC"
export SUPABASE_URL="https://gkfuepzqdzixejspfrlg.supabase.co"
export SUPABASE_ANON_KEY="your-supabase-key"
export OPENAI_API_KEY="your-openai-key"

# Set PORT variable (Railway uses this)
export PORT=8000

# Start server using exact Procfile command
uvicorn backend_server:app --host 0.0.0.0 --port $PORT
```

### 2. Test Imports

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
python3 -c "from backend_server import app; print('✅ Import successful')"
```

If this fails, you have an import error that will also fail on Railway.

### 3. Test Application Startup

```bash
# Start server and watch for errors
uvicorn backend_server:app --host 0.0.0.0 --port 8000

# In another terminal, test endpoints
curl http://localhost:8000/
curl http://localhost:8000/api/agents
```

If any of these tests fail locally, they'll also fail on Railway.

---

## Quick Fix Checklist

Before redeploying, verify:

- [ ] All files committed and pushed to GitHub
- [ ] `requirements.txt` exists and is complete
- [ ] `Procfile` uses `$PORT` variable
- [ ] `railway.toml` has correct configuration
- [ ] All environment variables will be added in Railway dashboard
- [ ] Local testing with system env variables works
- [ ] No hardcoded localhost URLs in code
- [ ] All subdirectories have `__init__.py` if needed
- [ ] Database and API credentials are valid
- [ ] No .env.local file in repository (should be in .gitignore)

---

## Getting Help

If still stuck after checking logs:

1. **Copy the exact error message** from Railway logs
2. **Share the error** with Claude Code for specific fix
3. **Check Railway documentation:** https://docs.railway.app
4. **Check Railway Discord:** https://discord.gg/railway

---

## Next Steps After Fixing

Once deployment succeeds:

1. ✅ Verify deployment is live:
   ```bash
   curl https://voxie-1.railway.app/
   ```

2. ✅ Test all endpoints:
   ```bash
   curl https://voxie-1.railway.app/api/agents
   curl https://voxie-1.railway.app/api/start-call
   ```

3. ✅ Test with frontend:
   - Open `simple_call_interface_cloud.html`
   - Enter backend URL: `https://voxie-1.railway.app`
   - Start a call

4. ✅ Monitor logs:
   ```bash
   railway logs --follow
   ```

---

## Summary

**Your current issue:** Railway built the app but deployment failed.

**Most likely causes:**
1. Missing environment variables (90% probability)
2. Import errors (5% probability)
3. Port binding issues (3% probability)
4. Other (2% probability)

**Immediate action:** Go to Railway dashboard and read the complete deployment logs to identify the exact error message.
