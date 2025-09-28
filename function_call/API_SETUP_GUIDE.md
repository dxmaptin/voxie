# 🔧 Setup Instructions for Real Voice Testing

## ❌ Current Issue: Invalid OpenAI API Key

The error you're seeing is because the `.env.local` file has a test API key instead of a real one:

```
ERROR: Incorrect API key provided: test-key**************ting
```

## ✅ How to Fix:

### 1. Get a Real OpenAI API Key

1. **Go to:** https://platform.openai.com/account/api-keys
2. **Sign in** to your OpenAI account (or create one)
3. **Click "Create new secret key"**
4. **Copy the key** (starts with `sk-...`)

### 2. Update Your Environment File

Edit `/Users/dxma/Desktop/voxie-clean/voxie-test/.env.local`:

```bash
# Replace the test key with your real OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### 3. Test the Voice Agent

After updating the API key:

```bash
cd /Users/dxma/Desktop/voxie-clean/voxie-test
uv run python src/agent.py console
```

## 🎯 What You'll See When It Works:

1. **Voxie starts up** and greets you
2. **You speak:** "Create a pizza restaurant agent for Mario's Pizza"
3. **Voxie responds** and starts creating the agent
4. **Real-time logs appear** in your terminal:

```
🎯 Starting agent creation for: Mario's Pizza
📡 Real-time events will appear below:
==================================================
📡 [14:32:15.585] scenario:started - Analyzing your business requirements...
📡 [14:32:17.587] scenario:completed - Business type determined: Restaurant
📡 [14:32:17.588] prompts:started - Creating custom prompts for restaurant agent...
📡 [14:32:19.590] prompts:completed - Prompts created for restaurant agent
📡 [14:32:19.591] voice:started - Setting up voice profile... | Agent: Mario's Pizza Restaurant Assistant
📡 [14:32:20.592] voice:completed - Voice profile ready - alloy | Voice: alloy
📡 [14:32:20.593] knowledge_base:started - Setting up knowledge base access...
📡 [14:32:20.594] knowledge_base:completed - Knowledge base connected
📡 [14:32:20.595] overall:completed - Agent creation successful!
============================================================
🎉 Agent Creation Completed Successfully!
✅ Agent Name: Mario's Pizza Restaurant Assistant
============================================================
```

## 🧪 Alternative: Test Without Voice

If you don't want to set up OpenAI API key right now, you can still test the agent creation pipeline directly:

```bash
cd /Users/dxma/Desktop/voxie-clean/function_call
python test_local_verification.py
```

This will show you the same real-time events without needing voice features.

## 💰 OpenAI API Costs

- **Realtime API:** ~$0.06 per minute of audio
- **Text completion:** ~$0.002 per 1K tokens
- Testing will cost very little (probably < $1)

## 🔒 Security Note

- Never commit your API key to git
- The `.env.local` file should be in your `.gitignore`
- Keep your API key private

## ❓ Need Help?

If you have issues:
1. Check your OpenAI account has credits
2. Verify the API key is copied correctly (no extra spaces)
3. Make sure you're using the right environment file path