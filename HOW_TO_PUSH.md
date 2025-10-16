# How to Push to GitHub - Fix Permission Denied Error

## Current Status

✅ **Two critical fixes are committed locally:**
1. ✅ Added `function_call/__init__.py` (fixes import errors)
2. ✅ Simplified `requirements.txt` (fixes pip install failure)

❌ **Cannot push to GitHub:** Permission denied error

---

## Commits Ready to Push

```bash
985c6a4 Fix Railway pip install failure: Simplify requirements.txt
55007d2 Fix Railway deployment: Add missing __init__.py to function_call package
```

These commits will fix your Railway deployment!

---

## Option 1: Using Personal Access Token (Recommended)

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Voxie Railway Deployment"
4. Select scopes:
   - ✅ **repo** (Full control of private repositories)
   - ✅ **workflow** (Update GitHub Action workflows)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 2: Push Using Token

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Push using token (replace YOUR_TOKEN with the token you copied)
git push https://YOUR_TOKEN@github.com/mmamuhammad2006/voxie.git malik-branch-ex2
```

**Example:**
```bash
# If your token is: ghp_abc123xyz789
git push https://ghp_abc123xyz789@github.com/mmamuhammad2006/voxie.git malik-branch-ex2
```

---

## Option 2: Using SSH Keys

If you have SSH keys configured:

### Step 1: Change Remote to SSH

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Change remote URL to SSH
git remote set-url origin git@github.com:mmamuhammad2006/voxie.git

# Verify
git remote -v
```

Should show:
```
origin  git@github.com:mmamuhammad2006/voxie.git (fetch)
origin  git@github.com:mmamuhammad2006/voxie.git (push)
```

### Step 2: Push

```bash
git push origin malik-branch-ex2
```

---

## Option 3: Using GitHub CLI

If you have GitHub CLI installed:

### Install (if needed)

```bash
# On macOS
brew install gh
```

### Authenticate and Push

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Login to GitHub
gh auth login
# Follow the prompts to authenticate

# Push
git push origin malik-branch-ex2
```

---

## Option 4: Push from GitHub Desktop

If you have GitHub Desktop installed:

1. Open GitHub Desktop
2. Select the "voxie" repository
3. You should see your commits in the "Changes" view
4. Click "Push origin" button

---

## Verify Push Succeeded

After pushing successfully, verify on GitHub:

### Option 1: GitHub Website
1. Go to: https://github.com/mmamuhammad2006/voxie
2. Switch to branch: `malik-branch-ex2`
3. Check that you see the latest commits:
   - "Fix Railway pip install failure: Simplify requirements.txt"
   - "Fix Railway deployment: Add missing __init__.py"

### Option 2: Command Line
```bash
git fetch origin
git log origin/malik-branch-ex2 --oneline -5
```

Should show your recent commits.

---

## After Successful Push

Railway will automatically detect the new commits and start deploying!

### 1. Watch Railway Dashboard

Go to: https://railway.app

You should see:
- New deployment starting automatically
- Build logs showing Python detection
- Package installation succeeding this time
- Application starting successfully

### 2. Expected Success Output

```
✓ Detected Python project
✓ Found requirements.txt
✓ Installing dependencies...
  → pip install -r requirements.txt
  → Installing fastapi==0.115.0
  → Installing uvicorn[standard]==0.32.0
  → Installing supabase==2.9.0
  → Installing livekit-agents==1.2.7 (WITHOUT problematic extras)
✓ Dependencies installed successfully
✓ Starting application...
  → uvicorn backend_server:app --host 0.0.0.0 --port $PORT
✓ Application startup complete
✓ Deployment successful
```

### 3. Add Environment Variables

Once deployment succeeds:

1. Go to Railway dashboard → voxie-1 → Variables
2. Add your environment variables (from .env.local)
3. Click "Deploy" to restart

### 4. Test Deployment

```bash
curl https://voxie-1.railway.app/
curl https://voxie-1.railway.app/api/agents
```

---

## Troubleshooting

### "Permission denied" persists

**Cause:** Your GitHub credentials are outdated or incorrect.

**Solutions:**
1. Use Personal Access Token (Option 1 above) - most reliable
2. Check if you have SSH keys: `ls -la ~/.ssh/`
3. Reconfigure Git credentials:
   ```bash
   git config --global credential.helper osxkeychain
   ```

### "Token not found" or "Bad credentials"

**Cause:** Token is incorrect or has wrong permissions.

**Solution:**
1. Generate a new token at https://github.com/settings/tokens
2. Make sure **repo** scope is checked
3. Copy and use the new token

### SSH "Permission denied (publickey)"

**Cause:** No SSH keys or keys not added to GitHub.

**Solution:**
1. Check for keys: `ls -la ~/.ssh/id_*.pub`
2. If no keys, generate one:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
3. Add to GitHub: https://github.com/settings/ssh/new
4. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
5. Paste into GitHub

---

## Quick Reference

**I want to:** Push using a token
**Command:**
```bash
git push https://YOUR_TOKEN@github.com/mmamuhammad2006/voxie.git malik-branch-ex2
```

**I want to:** Switch to SSH and push
**Commands:**
```bash
git remote set-url origin git@github.com:mmamuhammad2006/voxie.git
git push origin malik-branch-ex2
```

**I want to:** Use GitHub CLI
**Commands:**
```bash
gh auth login
git push origin malik-branch-ex2
```

---

## Summary

**Problem:** Permission denied when pushing to GitHub
**Cause:** HTTPS authentication not configured
**Solution:** Use Personal Access Token, SSH, or GitHub CLI
**Result:** Commits pushed → Railway auto-deploys → Backend goes live! 🚀

**Your commits are safe locally** - they just need to be pushed to trigger Railway deployment.
