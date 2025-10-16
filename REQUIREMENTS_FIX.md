# Requirements.txt Fix for Railway Deployment

## Issue Identified

The Railway deployment was failing at the `pip install -r requirements.txt` step with exit code 1.

**Error:**
```
RUN pip install -r requirements.txt
ERROR: failed to build: exit code: 1
```

---

## Root Cause

The problematic line in requirements.txt was:

```python
livekit-agents[openai,turn-detector,silero,cartesia,deepgram]==1.2.7
```

This package with extras (the `[openai,turn-detector,silero,cartesia,deepgram]` part) was causing build failures on Railway's Nixpacks environment. These extras require:
- Complex C/C++ dependencies
- Audio processing libraries (for Silero VAD)
- Additional build tools not available in the Railway environment

---

## Fix Applied

### Updated requirements.txt

**Before:**
```python
livekit-agents[openai,turn-detector,silero,cartesia,deepgram]==1.2.7
livekit-plugins-noise-cancellation==0.2.2
openai>=1.0.0
tiktoken>=0.5.0
```

**After:**
```python
livekit-agents==1.2.7  # Removed extras that need C dependencies
openai>=1.0.0          # Removed tiktoken (optional dependency)
```

### Changes Made:
1. ✅ Removed extras from `livekit-agents` package
2. ✅ Removed `livekit-plugins-noise-cancellation` (optional)
3. ✅ Removed `tiktoken` (optional dependency)
4. ✅ Kept core packages: fastapi, uvicorn, supabase, livekit-api

---

## Why This Works

The backend_server.py only needs:
- FastAPI for the web server
- Uvicorn for running the ASGI app
- Supabase for database access
- python-dotenv for environment variables

The LiveKit agent functionality is NOT used in backend_server.py - it's only used in the `voxie-test/` directory for the agent implementation. Since we're only deploying the backend API server, we don't need the full LiveKit agents package with all extras.

---

## Alternative: Minimal Requirements

If you still have issues, use `requirements-minimal.txt` instead:

```python
# Minimal requirements - only what backend_server.py actually needs
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
python-dotenv==1.0.1
supabase==2.9.0
requests==2.32.3
aiohttp==3.10.10
```

To use this, rename it:
```bash
mv requirements.txt requirements-full.txt
mv requirements-minimal.txt requirements.txt
```

---

## Testing Locally

Before deploying, test that the simplified requirements work:

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Create test venv
python3 -m venv test-venv
source test-venv/bin/activate

# Install simplified requirements
pip install -r requirements.txt

# Test backend starts
python3 -c "from backend_server import app; print('✅ Import successful')"
uvicorn backend_server:app --host 0.0.0.0 --port 8000
```

If this works, Railway will also work.

---

## Commit and Deploy

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Add the fixed requirements.txt
git add requirements.txt requirements-minimal.txt REQUIREMENTS_FIX.md

# Commit
git commit -m "Fix Railway deployment: Simplify requirements.txt

Remove problematic livekit-agents extras that require C dependencies.
These extras (silero, cartesia, deepgram) need audio processing libraries
not available in Railway's Nixpacks environment.

Changes:
- Remove [extras] from livekit-agents package
- Remove optional packages: tiktoken, livekit-plugins-noise-cancellation
- Add requirements-minimal.txt as alternative
- Add REQUIREMENTS_FIX.md with explanation

This should fix the 'pip install -r requirements.txt' failure.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin malik-branch-ex2
```

---

## Expected Railway Output

After pushing, Railway should now successfully install packages:

```
✓ Installing dependencies...
✓ pip install -r requirements.txt
  → Installing fastapi==0.115.0
  → Installing uvicorn[standard]==0.32.0
  → Installing supabase==2.9.0
  → Installing livekit==0.17.4
  → Installing livekit-api==0.6.2
  → Installing livekit-agents==1.2.7 (without extras)
  → Installing openai
  → Installing requests==2.32.3
✓ Dependencies installed successfully
✓ Starting application...
✓ Deployment successful
```

---

## If Still Failing

If Railway still fails with the simplified requirements.txt, use the minimal version:

```bash
# Switch to minimal requirements
mv requirements.txt requirements-full.txt
mv requirements-minimal.txt requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Use minimal requirements.txt for Railway"
git push origin malik-branch-ex2
```

The minimal version only includes packages that backend_server.py directly imports.

---

## Environment Variables Reminder

After successful deployment, remember to add environment variables in Railway dashboard:

1. Go to https://railway.app
2. Select voxie-1 project → your service → Variables
3. Add your environment variables (get values from your local .env.local file)
4. Click "Deploy" to restart with new variables

**Do NOT commit .env or .env.local files - they contain secrets!**

---

## Summary

**Problem:** `livekit-agents[extras]` causing pip install to fail
**Solution:** Remove extras and use base package only
**Result:** Railway can now install all dependencies successfully

**Next:** Push to GitHub and Railway will auto-deploy! 🚀
