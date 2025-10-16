# Troubleshooting Guide - Exercise 4

## Common Issue: "Could not import module 'backend_server'"

### Problem

When you tried running:
```bash
uvicorn backend_server:app --host 0.0.0.0 --port 8000
```

You got:
```
ERROR: Error loading ASGI app. Could not import module "backend_server".
```

### Root Cause

You were in the **wrong directory**: `voxie-test/` instead of `voxie/`

### Solution

**Always run backend commands from the `voxie` directory, NOT `voxie-test`!**

```bash
# Check where you are
pwd

# If you see: /Users/muhammad/.../voxie-test
# You're in the WRONG place!

# Go up one level:
cd ..

# Verify you're now in voxie:
pwd
# Should show: /Users/muhammad/.../Voxie/voxie

# Now run the backend:
python backend_server.py
```

---

## Directory Structure Explained

```
Voxie/
└── voxie/                              ← Run backend commands HERE
    ├── backend_server.py              ← Main backend
    ├── requirements.txt               ← Dependencies
    ├── Procfile                       ← Start command
    ├── simple_agent.py                ← Agent runner
    ├── function_call/                 ← Supporting modules
    └── voxie-test/                    ← DO NOT run backend from here!
        └── src/
            └── agent.py               ← Agent implementation only
```

**Key Rule:**
- Backend commands: Run from `/voxie` ✅
- Agent testing: Run from `/voxie-test` ✅
- Backend from voxie-test: ❌ WILL NOT WORK

---

## Quick Fix Commands

### If you get the import error:

```bash
# 1. Check your location
pwd

# 2. If in voxie-test, go up:
cd ..

# 3. Verify you see backend_server.py:
ls backend_server.py

# 4. Run backend:
python backend_server.py
```

---

## About Uvicorn

### "I don't have uvicorn"

**Actually, you do!** It's in `requirements.txt`:

```bash
# Check requirements.txt
cat requirements.txt | grep uvicorn
# Shows: uvicorn[standard]==0.32.0
```

### Installing Uvicorn

If you need to install it locally:

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
pip install -r requirements.txt
```

Or just uvicorn:
```bash
pip install "uvicorn[standard]"
```

### Testing Uvicorn Installation

```bash
# Check if installed
python -c "import uvicorn; print(uvicorn.__version__)"

# Should show: 0.32.0 (or similar)

# Try running:
python -m uvicorn --version
```

---

## Railway Deployment - Why It Will Work

### "But uvicorn doesn't work on my machine!"

**That's okay!** Here's why Railway will work:

1. **Railway installs dependencies automatically:**
   ```bash
   # Railway runs this automatically:
   pip install -r requirements.txt
   ```
   This installs `uvicorn[standard]==0.32.0`

2. **Railway uses the Procfile command:**
   ```bash
   # From Procfile:
   uvicorn backend_server:app --host 0.0.0.0 --port $PORT
   ```

3. **Railway sets the correct directory:**
   Railway automatically runs commands from the project root (`/voxie`)

4. **Railway provides the PORT variable:**
   Railway automatically sets `$PORT` environment variable

### Testing Locally (Optional)

If you want to test the exact command Railway uses:

```bash
# Go to voxie directory
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Install dependencies
pip install -r requirements.txt

# Run the Procfile command (use port 8000 instead of $PORT)
uvicorn backend_server:app --host 0.0.0.0 --port 8000
```

But it's **not required** to test locally! You can deploy directly to Railway.

---

## Alternative: Use Python Directly

If you prefer to test locally using Python (not uvicorn):

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
python backend_server.py
```

This works because `backend_server.py` has this at the end:

```python
if __name__ == "__main__":
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

---

## What Railway Does vs What You Need to Do

| Step | Railway (Automatic) | You (Manual) |
|------|---------------------|--------------|
| Go to project directory | ✅ Automatic | ✅ Must do: `cd voxie` |
| Install dependencies | ✅ Auto: `pip install -r requirements.txt` | ✅ Must do if testing locally |
| Set PORT variable | ✅ Auto: Railway provides `$PORT` | ❌ Use 8000 for local |
| Run Procfile command | ✅ Auto: Runs `uvicorn backend_server:app...` | ⚠️ Optional for local testing |
| Set environment variables | ✅ Via Railway dashboard | ✅ Already in `.env.local` |

---

## Summary

### The Issue You Had:

```bash
# You were here:
(voxie) muhammad@Muhammads-MacBook-Pro-2 voxie-test %

# Running this:
uvicorn backend_server:app --host 0.0.0.0 --port 8000

# ERROR: backend_server.py is not in voxie-test!
```

### The Fix:

```bash
# Go to parent directory:
cd ..

# Now you're here:
(voxie) muhammad@Muhammads-MacBook-Pro-2 voxie %

# Now it works:
python backend_server.py
# Or:
uvicorn backend_server:app --host 0.0.0.0 --port 8000
```

---

## For Railway Deployment

**You don't need to worry about any of this!**

Railway will:
1. ✅ Be in the correct directory automatically
2. ✅ Install uvicorn from `requirements.txt`
3. ✅ Run the Procfile command correctly
4. ✅ Set all environment variables from dashboard

**Just deploy and it will work!**

---

## Quick Test Before Deployment (Optional)

```bash
# 1. Go to correct directory
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# 2. Verify backend_server.py exists
ls backend_server.py

# 3. Run backend
python backend_server.py

# 4. In new terminal, test:
curl http://localhost:8000/
```

If this works, Railway will work too!

---

## Still Having Issues?

### Check Python environment:
```bash
which python
python --version
# Should be Python 3.9+
```

### Check virtual environment:
```bash
# If using venv
source .venv/bin/activate
# Or
source venv/bin/activate
```

### Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Check working directory:
```bash
pwd
ls backend_server.py
# If "No such file", you're in wrong directory!
```

---

## Ready to Deploy?

Skip local testing and deploy directly to Railway:

```bash
# Commit everything
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
git add .
git commit -m "Exercise 4: Backend ready for Railway"
git push origin main

# Then deploy via Railway dashboard
```

Railway handles everything automatically - no need to test uvicorn locally!

---

## Key Takeaway

❌ **Don't run backend from `voxie-test/`**
✅ **Always run backend from `voxie/`**
✅ **Railway will handle uvicorn automatically**
✅ **Local testing is optional - can deploy directly**
