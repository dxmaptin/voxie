# Real-time Agent Creation Testing Guide

## 🚀 Complete Test Suite

This directory contains comprehensive tests for the real-time agent creation system with detailed logging.

## 📋 Prerequisites

1. **Install Dependencies:**
   ```bash
   chmod +x setup_test_environment.sh
   ./setup_test_environment.sh
   ```

2. **Verify Environment:**
   ```bash
   python --version  # Should be 3.9+
   pip list | grep livekit  # Should show LiveKit packages
   ```

## 🧪 Test Suite Overview

### 1. Local Verification Test ⭐ **START HERE**
**File:** `test_local_verification.py`

**What it does:**
- Tests direct agent creation without WebSocket
- Generates detailed logs with timestamps
- Verifies all pipeline steps work correctly
- Creates JSON files with captured events

**Run:**
```bash
python test_local_verification.py
```

**Expected Output:**
```
[14:32:15.123] INFO: 🚀 Starting Local Verification Test
[14:32:15.124] INFO: 📦 Step 1: Importing required modules...
[14:32:15.234] INFO: ✅ LiveKit agent modules imported successfully
[14:32:15.235] INFO: 🔧 Step 2: Setting up event capture system...
[14:32:15.236] INFO: ✅ Event capture system ready
[14:32:15.237] INFO: 🎯 Step 3: Creating test requirements...
[14:32:15.238] INFO:    Business Name: Local Test Echo Pizza
[14:32:15.239] INFO:    Business Type: pizza restaurant
[14:32:15.240] INFO: ⚡ Step 5: Running agent creation pipeline...
[14:32:15.241] EVENT: 📡 scenario:started - Analyzing your business requirements...
[14:32:17.245] EVENT: 📡 scenario:completed - Business type determined: Pizza
[14:32:17.246] EVENT: 📡 prompts:started - Creating custom prompts for pizza agent...
[14:32:19.250] EVENT: 📡 prompts:completed - Prompts created for pizza agent
[14:32:19.251] EVENT: 📡 voice:started - Setting up voice profile... | Agent: Local Test Echo Pizza Pizza Assistant
[14:32:19.252] EVENT: 📡 knowledge_base:started - Setting up knowledge base access...
[14:32:20.255] EVENT: 📡 voice:completed - Voice profile ready | Agent: Local Test Echo Pizza Pizza Assistant | Voice: echo
[14:32:20.256] EVENT: 📡 knowledge_base:completed - Knowledge base connected
[14:32:20.257] EVENT: 📡 overall:completed - Agent creation successful!
[14:32:20.258] SUCCESS: ✅ Agent creation completed successfully!
[14:32:20.259] SUCCESS:    Duration: 5.02 seconds
[14:32:20.260] INFO:    Agent Type: Local Test Echo Pizza Pizza Assistant
[14:32:20.261] INFO:    Voice Model: echo
[14:32:20.262] SUCCESS: ✅ ALL TESTS PASSED!
```

### 2. Complete Integration Test
**File:** `test_complete_integration.py`

**What it does:**
- Tests all components: Direct creation, AgentManager, Event broadcasting
- Creates comprehensive logs and JSON files
- Verifies SocketIO emissions
- Tests error handling

**Run:**
```bash
python test_complete_integration.py
```

### 3. WebSocket Client Test
**File:** `test_websocket_client.py`

**What it does:**
- Tests real WebSocket communication
- Connects to webhook server and sends requests
- Monitors real-time events
- Verifies end-to-end communication

**Run:**
```bash
# First, start your webhook server:
python webhook_server.py

# Then in another terminal:
python test_websocket_client.py
```

## 📊 Log Files Generated

All tests create detailed log files in the `logs/` directory:

- `local_verification_YYYYMMDD_HHMMSS.log` - Detailed test execution log
- `events_YYYYMMDD_HHMMSS.json` - All captured events in JSON format
- `agent_spec_YYYYMMDD_HHMMSS.json` - Generated agent specifications
- `websocket_events_YYYYMMDD_HHMMSS.json` - WebSocket events received

## 🔍 What to Look For

### ✅ Success Indicators:
1. **All events generated:** scenario → prompts → voice → knowledge_base → overall
2. **Voice model configured:** Should show "echo" for pizza restaurants
3. **Agent specifications:** Complete with name, voice, functions
4. **No errors:** No exceptions or error messages in logs

### ❌ Failure Indicators:
1. **Import errors:** Missing LiveKit dependencies
2. **Missing events:** Incomplete event sequence
3. **Exceptions:** Python errors in the logs
4. **WebSocket failures:** Connection or communication issues

## 🐛 Troubleshooting

### Common Issues:

1. **ModuleNotFoundError: 'livekit'**
   ```bash
   pip install livekit-agents[openai,turn-detector,silero,cartesia,deepgram]
   pip install livekit-plugins-noise-cancellation
   ```

2. **No events captured**
   - Check if event broadcaster is properly initialized
   - Verify ProcessingAgent is created with broadcaster parameter

3. **WebSocket connection failed**
   - Ensure webhook server is running on correct port
   - Check firewall/network settings

4. **Agent creation timeout**
   - Check internet connection (for OpenAI API)
   - Verify .env.local has valid API keys

## 📋 For Frontend Integration

After tests pass, your frontend should:

1. **Connect to WebSocket:**
   ```javascript
   const socket = io('http://localhost:5000');
   ```

2. **Listen for events:**
   ```javascript
   socket.on('agent_creation_update', (data) => {
     console.log(`${data.step}:${data.status} - ${data.message}`);
     if (data.voice_model) console.log(`Voice: ${data.voice_model}`);
     if (data.agent_name) console.log(`Agent: ${data.agent_name}`);
   });
   ```

3. **Start agent creation:**
   ```javascript
   socket.emit('start_agent_creation', {
     session_id: 'unique-session-id',
     requirements: {
       business_name: 'My Pizza Shop',
       business_type: 'pizza restaurant',
       voice_model: 'echo'
     }
   });
   ```

## 🎯 Expected Event Flow

```
scenario:started → scenario:completed →
prompts:started → prompts:completed →
voice:started → voice:completed →
knowledge_base:started → knowledge_base:completed →
overall:completed
```

Each event includes:
- `step`: The current pipeline step
- `status`: started/completed/failed
- `message`: Human-readable description
- `agent_name`: Generated agent name (when available)
- `voice_model`: Configured voice model (when available)
- `error`: Error details (if failed)

## 📞 Support

If tests fail:
1. Check the generated log files for detailed error information
2. Verify all dependencies are installed correctly
3. Ensure .env.local has proper configuration
4. Run tests individually to isolate issues