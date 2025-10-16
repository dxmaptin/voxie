# Local Testing Guide for Exercise 4

## Testing Backend Locally Before Deployment

Before deploying to Railway, test your backend locally to ensure everything works.

---

## Prerequisites

Make sure you're in the correct directory:
```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
pwd
# Should show: /Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie
```

**IMPORTANT:** Do NOT run commands from `voxie-test/` directory!

---

## Method 1: Using Python Directly (Recommended for Local Testing)

```bash
# From the voxie directory:
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Run the backend server
python backend_server.py
```

**Expected output:**
```
✅ Loaded environment from .env.local
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
🚀 Backend server starting...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Method 2: Using Uvicorn Command (Same as Railway)

```bash
# Install uvicorn if needed (already in requirements.txt)
pip install uvicorn[standard]

# Run using uvicorn (this is what Railway uses)
python -m uvicorn backend_server:app --host 0.0.0.0 --port 8000

# Or using the uvicorn command directly:
uvicorn backend_server:app --host 0.0.0.0 --port 8000
```

**Note:** Both methods work the same way. Railway uses the uvicorn command.

---

## Common Errors and Fixes

### Error: "Could not import module 'backend_server'"

**Cause:** You're in the wrong directory (probably `voxie-test/`)

**Fix:**
```bash
# Check current directory
pwd

# Should be:
/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie

# If in voxie-test, go up one level:
cd ..
pwd
# Now should show the voxie directory

# Then run:
python backend_server.py
```

---

### Error: "Address already in use" (Port 8000)

**Cause:** Backend is already running

**Fix:**
```bash
# Find the process using port 8000
lsof -ti:8000

# Kill it
kill $(lsof -ti:8000)

# Or use a different port:
python -m uvicorn backend_server:app --host 0.0.0.0 --port 8001
```

---

### Error: "No module named 'fastapi'"

**Cause:** Dependencies not installed

**Fix:**
```bash
# Activate virtual environment if you have one
source .venv/bin/activate  # or: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Then run:
python backend_server.py
```

---

## Testing Endpoints

Once the server is running, test in a new terminal:

### Test 1: Health Check
```bash
curl http://localhost:8000/
```

**Expected:**
```json
{
  "status": "ok",
  "service": "voxie-backend",
  "timestamp": "2025-..."
}
```

### Test 2: Agents API
```bash
curl http://localhost:8000/api/agents
```

**Expected:**
```json
{
  "status": "success",
  "count": 33,
  "agents": [...]
}
```

### Test 3: Analytics
```bash
curl http://localhost:8000/api/analytics/summary
```

---

## Testing with Frontend

### Option 1: Auto-Detecting Frontend (Localhost)
```bash
# Open in browser
open simple_call_interface.html
```

This automatically uses `http://localhost:8000` when opened locally.

### Option 2: Cloud-Configured Frontend (Manual URL)
```bash
# Temporarily change the URL for local testing
open simple_call_interface_cloud.html
```

Change the URL to `http://localhost:8000` in the input field.

---

## Verifying Environment Variables

Check that environment variables are loaded:

```bash
# Start the backend and check logs
python backend_server.py

# You should see:
✅ Loaded environment from .env.local
```

If you see `⚠️ No .env file found`, check:
```bash
# List .env files
ls -la | grep env

# Should see:
.env.local
.env.example
```

---

## Directory Structure Check

Make sure you're in the right place:

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Check structure
ls -la

# Should see:
backend_server.py          ← Main server
requirements.txt           ← Dependencies
Procfile                   ← Railway start command
railway.toml               ← Railway config
simple_agent.py            ← Agent runner
function_call/             ← Supporting modules
voxie-test/                ← Agent implementation
```

---

## What Railway Will Do

When you deploy to Railway, it will:

1. **Detect Python project** from `requirements.txt`
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the start command from Procfile:**
   ```bash
   uvicorn backend_server:app --host 0.0.0.0 --port $PORT
   ```
4. **Set environment variables** from Railway dashboard
5. **Expose on public URL:** `https://voxie-1.railway.app`

---

## Simulating Railway Locally

Test exactly how Railway will run your app:

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Install dependencies (Railway does this)
pip install -r requirements.txt

# Run using the Procfile command (Railway does this)
PORT=8000 uvicorn backend_server:app --host 0.0.0.0 --port $PORT
```

---

## Stopping the Server

### If running in foreground:
Press `Ctrl+C`

### If running in background:
```bash
# Find process
ps aux | grep backend_server

# Or find by port
lsof -ti:8000

# Kill it
kill $(lsof -ti:8000)
```

---

## Quick Test Script

Save this as `test_local.sh`:

```bash
#!/bin/bash

echo "🧪 Testing Local Backend"
echo "======================="
echo ""

# Test health
echo "Test 1: Health Check"
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

# Test agents
echo "Test 2: Agents API"
curl -s http://localhost:8000/api/agents | python3 -m json.tool | head -20
echo ""

echo "✅ Local backend is working!"
```

Run it:
```bash
chmod +x test_local.sh
./test_local.sh
```

---

## Debugging Tips

### Check if server is running:
```bash
curl http://localhost:8000/
# If connection refused, server is not running
```

### Check server logs:
Look at the terminal where you ran `python backend_server.py`

### Check which directory you're in:
```bash
pwd
ls backend_server.py
# Should see the file
```

### Check Python version:
```bash
python --version
# Should be Python 3.9+
```

---

## Ready to Deploy?

Once local testing works:

1. ✅ Backend runs without errors
2. ✅ Health endpoint returns `{"status": "ok"}`
3. ✅ Agents API returns data
4. ✅ Frontend can connect locally

**You're ready to deploy to Railway!**

Follow `DEPLOY_NOW.md` for deployment instructions.

---

## Common Issues Summary

| Error | Cause | Fix |
|-------|-------|-----|
| "Could not import backend_server" | Wrong directory | `cd` to `/voxie`, not `/voxie-test` |
| "Address already in use" | Server already running | `kill $(lsof -ti:8000)` |
| "No module named 'fastapi'" | Missing dependencies | `pip install -r requirements.txt` |
| "⚠️ No .env file found" | Missing .env.local | Check `.env.local` exists |
| Connection refused | Server not running | Run `python backend_server.py` |

---

## Summary

**To test locally:**
```bash
# 1. Go to correct directory
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# 2. Run backend
python backend_server.py

# 3. Test in new terminal
curl http://localhost:8000/
curl http://localhost:8000/api/agents

# 4. Test with frontend
open simple_call_interface.html
```

**Once working locally, deploy to Railway!**
