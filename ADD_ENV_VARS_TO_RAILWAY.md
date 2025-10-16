# 🔐 Add Environment Variables to Railway

## Current Error

```json
{
  "detail": "Error fetching agents: SUPABASE_URL and SUPABASE_ANON_KEY must be set"
}
```

**Cause:** Environment variables are not set in Railway dashboard.

**Your deployment is LIVE** ✅ - it just needs the configuration!

---

## Step-by-Step: Add Environment Variables

### Step 1: Get Your Environment Variables

Open your local `.env.local` file and copy the values:

```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"
cat .env.local
```

You'll see something like:
```bash
LIVEKIT_URL=wss://voxie-1-f00463v2.livekit.cloud
LIVEKIT_API_KEY=APIWuHiyFH89Kfq
LIVEKIT_API_SECRET=fJdLQdTbskjgKjtynmF8RIifIeDiFLRHif5k0VLoeDZC
SUPABASE_URL=https://gkfuepzqdzixejspfrlg.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
```

**Copy these values** - you'll need them in the next step.

---

### Step 2: Open Railway Dashboard

1. Go to: **https://railway.app**
2. Log in if needed
3. Click on **"voxie-1"** project
4. Click on your **service** (the one that's deployed)

---

### Step 3: Add Variables

1. In the service view, click on the **"Variables"** tab (left sidebar)
2. Click **"+ New Variable"** or **"Add Variable"**
3. Add each variable one by one:

#### Required Variables (from your .env.local):

**Variable 1:**
- Key: `SUPABASE_URL`
- Value: `https://gkfuepzqdzixejspfrlg.supabase.co`

**Variable 2:**
- Key: `SUPABASE_ANON_KEY`
- Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (your full key)

**Variable 3:**
- Key: `LIVEKIT_URL`
- Value: `wss://voxie-1-f00463v2.livekit.cloud`

**Variable 4:**
- Key: `LIVEKIT_API_KEY`
- Value: `APIWuHiyFH89Kfq`

**Variable 5:**
- Key: `LIVEKIT_API_SECRET`
- Value: `fJdLQdTbskjgKjtynmF8RIifIeDiFLRHif5k0VLoeDZC`

**Variable 6:**
- Key: `OPENAI_API_KEY`
- Value: `sk-proj-...` (your full OpenAI key)

---

### Step 4: Deploy (Restart)

After adding all variables:

1. Click the **"Deploy"** button at the top
2. Or click **"Redeploy"** in the deployments tab
3. Wait 1-2 minutes for the service to restart

Railway will restart your application with the new environment variables.

---

## Step 5: Test Deployment

After redeployment completes:

### Test 1: Health Check
```bash
curl https://voxie-1.railway.app/
```

**Expected:**
```json
{
  "message": "Voxie Backend API",
  "status": "running",
  "version": "1.0.0"
}
```

### Test 2: Agents Endpoint
```bash
curl https://voxie-1.railway.app/api/agents
```

**Expected:**
```json
{
  "agents": [
    {"id": 1, "name": "Agent 1", ...},
    ...
  ]
}
```

If you see the agents data, **it works!** ✅

---

## Alternative: Using Railway CLI

If you prefer command line:

### Install Railway CLI
```bash
# macOS
brew install railway

# Or npm
npm install -g @railway/cli
```

### Add Variables via CLI
```bash
cd "/Users/muhammad/Personal/Projects/Personal Projects/Voxie/voxie"

# Login
railway login

# Link to your project
railway link

# Add variables
railway variables set SUPABASE_URL="https://gkfuepzqdzixejspfrlg.supabase.co"
railway variables set SUPABASE_ANON_KEY="your-key-here"
railway variables set LIVEKIT_URL="wss://voxie-1-f00463v2.livekit.cloud"
railway variables set LIVEKIT_API_KEY="APIWuHiyFH89Kfq"
railway variables set LIVEKIT_API_SECRET="your-secret-here"
railway variables set OPENAI_API_KEY="your-openai-key"

# Redeploy
railway up
```

---

## Troubleshooting

### Still getting "must be set" error?

**Check Railway Logs:**

1. Go to Railway dashboard
2. Click on your service
3. Click "Deployments" tab
4. Click on the latest deployment
5. Look for error messages in the logs

**Common issues:**

1. **Variables not saved:** Make sure you clicked "Deploy" after adding variables
2. **Typo in variable name:** Must be exact: `SUPABASE_URL` not `SUPABASE_URL_`
3. **Service not restarted:** Click "Redeploy" to restart with new vars

### How to verify variables are set?

In Railway dashboard → Variables tab, you should see:
```
SUPABASE_URL          ✓ Set
SUPABASE_ANON_KEY     ✓ Set
LIVEKIT_URL           ✓ Set
LIVEKIT_API_KEY       ✓ Set
LIVEKIT_API_SECRET    ✓ Set
OPENAI_API_KEY        ✓ Set
```

---

## After Variables Are Added

### Test with Frontend

1. Open `simple_call_interface_cloud.html` in browser
2. Backend URL should be: `https://voxie-1.railway.app`
3. Select an agent from the dropdown
4. Click "Start Call"
5. Should connect and work! ✅

---

## Security Note

- **Never commit** `.env` or `.env.local` files to Git
- Railway variables are encrypted and secure
- Variables are only accessible to your deployment
- You can rotate keys anytime in Railway dashboard

---

## Quick Reference

**Where to add variables:**
https://railway.app → voxie-1 → Your Service → Variables tab

**What variables to add:**
- SUPABASE_URL
- SUPABASE_ANON_KEY
- LIVEKIT_URL
- LIVEKIT_API_KEY
- LIVEKIT_API_SECRET
- OPENAI_API_KEY

**After adding:**
Click "Deploy" to restart

**Test:**
```bash
curl https://voxie-1.railway.app/api/agents
```

---

## Success Checklist

- [ ] Opened Railway dashboard
- [ ] Found voxie-1 project
- [ ] Clicked on service
- [ ] Opened Variables tab
- [ ] Added all 6 environment variables
- [ ] Clicked "Deploy" to restart
- [ ] Waited for deployment to complete
- [ ] Tested with curl
- [ ] Got successful response ✅

Once you add the variables and redeploy, your backend will work perfectly! 🚀
