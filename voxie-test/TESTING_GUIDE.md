# Agent Persistence Integration - Testing Guide

## ✅ Integration Complete!

The agent persistence system is now integrated into your Voxie agent. When you create an agent through Voxie, it will automatically save to your Supabase database.

## 🧪 Pre-Test Verification (PASSED ✅)

All tests passed successfully:
- ✅ Supabase connection working
- ✅ Can list existing agents (found 5 agents)
- ✅ Can save new agents
- ✅ Can load saved agents
- ✅ No deletion operations in code (as requested)

## 📋 How to Test Console Mode

### 1. Set your OpenAI API Key

Edit `.env.local` and add your OpenAI key:
```bash
cd /Users/dxma/Desktop/voxie-clean/voxie-test
# Edit .env.local and replace "your-openai-api-key-here" with your actual key
```

### 2. Run Console Mode

```bash
uv run python src/agent.py console
```

### 3. Talk to Voxie and Create an Agent

When the console starts, speak to Voxie like:

**Example Conversation:**
```
You: "Hi Voxie, I want to create an agent for my pizza restaurant"

Voxie: "Great! What's the name of your pizza restaurant?"

You: "Tony's Pizza Palace"

Voxie: "Wonderful! What kind of tone would you like your agent to have?"

You: "Casual and fun, like talking to a friend"

Voxie: "Perfect! What should your agent be able to do?"

You: "Take orders, answer menu questions, and check delivery status"

Voxie: "Excellent! Give me just a moment to create your agent..."

[Voxie processes...]

Voxie: "Your agent is ready to test! Would you like to try it?"
```

### 4. Check the Logs

While Voxie is processing, watch for these log messages:

```
✅ Processing complete! Created spec: Tony's Pizza Palace Restaurant Assistant
✅ Supabase connected: https://gkfuepzqdzixejspfrlg.supabase.co
✅ Agent saved: [some-uuid-here]
   Business: Tony's Pizza Palace
   Type: Pizza Restaurant
   Voice: echo
🔖 Agent saved to database with ID: [uuid]
   This agent can now be reproduced!
```

### 5. Verify in Database

After creating the agent, check your Supabase database:

```bash
# Run this to list all agents
cd /Users/dxma/Desktop/voxie-clean/voxie-test
python -c "
import sys
sys.path.append('src')
from agent_persistence import AgentPersistence

agents = AgentPersistence.list_agents(limit=10)
print(f'📊 Total agents: {len(agents)}\n')
for agent in agents:
    print(f'{agent[\"name\"]}')
    print(f'  Category: {agent[\"category\"]}')
    print(f'  Created: {agent[\"created_at\"][:19]}')
    print()
"
```

You should see your newly created agent at the top of the list!

## 🔍 What Gets Saved

When Voxie creates an agent, the following is saved to Supabase:

### User Requirements
- `business_name` - "Tony's Pizza Palace"
- `business_type` - "Pizza Restaurant"
- `tone` - "casual and fun"
- `target_audience` - Who the agent serves
- `main_functions` - ["take_order", "menu_inquiry", "delivery_status"]
- `contact_info` - Any contact details

### Processed Agent Spec
- `agent_type` - Full agent name
- `instructions` - Complete system prompt
- `voice` - OpenAI voice (alloy, echo, nova, etc.)
- `functions` - All available functions
- `sample_responses` - Example responses
- `business_context` - Business-specific data

### Metadata
- `session_id` - Console session identifier
- `room_id` - LiveKit room name
- `created_at` - Timestamp

## 🎯 Expected Behavior

1. **During Conversation**: Voxie collects all requirements
2. **During Processing**: Voxie creates agent spec
3. **Auto-Save**: System automatically saves to Supabase
4. **Logging**: You'll see confirmation in console logs
5. **Database**: Agent appears in Supabase `agents` table

## ⚠️ Important Notes

- **No Deletion**: Code has NO delete operations (as requested)
- **Test Agents**: All test agents remain in database
- **Error Handling**: If save fails, agent still works (non-critical)
- **Console Mode**: Use `console` mode for voice testing

## 🐛 Troubleshooting

If the save doesn't work:

1. **Check OpenAI Key**: Make sure it's set in `.env.local`
2. **Check Logs**: Look for error messages starting with `❌`
3. **Check Supabase**: Verify credentials in `.env.local`
4. **Check Network**: Ensure internet connection

## 📊 Verify Everything Works

Run the integration test again:
```bash
cd /Users/dxma/Desktop/voxie-clean/voxie-test
python src/test_integration.py
```

All tests should pass! ✅

---

**You're ready to test!** 🚀

Run `uv run python src/agent.py console` and create an agent through conversation with Voxie!
