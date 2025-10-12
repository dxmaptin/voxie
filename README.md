# Voxie - AI Voice Agent Platform

Voxie is an intelligent voice AI platform that helps businesses create custom voice agents. It features a multi-agent system where "Voxie" (the agent creator) guides users through building tailored voice agents for their specific business needs.

## 🌟 Features

- **Multi-Agent System**: Voxie creates and manages custom voice agents dynamically
- **Real-Time Voice Communication**: Powered by LiveKit for low-latency voice interactions
- **Agent Persistence**: Save and reproduce agents from database
- **Call Analytics**: Automatic call tracking, transcription, and AI-generated summaries
- **Knowledge Base Integration**: Agents can search and answer from company knowledge bases
- **Dashboard & API**: Full REST API with real-time SSE logging for frontend integration

## 📋 Prerequisites

- **Python 3.11+**
- **uv** (Python package installer) - [Install uv](https://github.com/astral-sh/uv)
- **Node.js 18+** (if using frontend dashboard)
- **Supabase Account** - [Create account](https://supabase.com)
- **LiveKit Cloud Account** - [Create account](https://livekit.io)
- **OpenAI API Key** - [Get API key](https://platform.openai.com)
- **Deepgram API Key** (optional, for transcription) - [Get API key](https://deepgram.com)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd voxie-clean
```

### 2. Install Dependencies

```bash
# Install Python dependencies using uv
uv pip install -r requirements.txt

# Install backend dependencies (for REST API server)
uv pip install -r requirements-backend.txt
```

### 3. Configure Environment Variables(Find everything in Notion or Ask daniel)

Create a `.env.local` file in the root directory:

```bash
# Supabase Configuration
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-supabase-anon-key"

# LiveKit Configuration
LIVEKIT_API_KEY="your-livekit-api-key"
LIVEKIT_API_SECRET="your-livekit-api-secret"
LIVEKIT_URL="wss://your-livekit-deployment.livekit.cloud"

# OpenAI Configuration
OPENAI_API_KEY="sk-proj-your-openai-api-key"

# Deepgram Configuration (Optional)
DEEPGRAM_API_KEY="your-deepgram-api-key"

# Agent Configuration (Optional - for loading specific agents)
AGENT_ID="agent-id-from-database"

# Backend Logging Configuration (Optional - for real-time status streaming)
ENABLE_BACKEND_LOGGING="true"
BACKEND_URL="http://localhost:8000"
```

### 4. Set Up Supabase Database

#### Create Required Tables

Run these SQL commands in your Supabase SQL editor:

```sql
-- Agents table (stores agent configurations)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_requirements JSONB NOT NULL,
    processed_spec JSONB NOT NULL,
    session_id TEXT,
    room_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Call sessions table (tracks all voice calls)
CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    agent_id UUID REFERENCES agents(id),
    room_name TEXT NOT NULL,
    primary_agent_type TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    call_status TEXT DEFAULT 'active',
    call_rating INTEGER,
    customer_sentiment TEXT,
    issue_resolved BOOLEAN,
    notes TEXT
);

-- Conversation turns table (tracks dialogue)
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_session_id UUID REFERENCES call_sessions(id),
    turn_number INTEGER NOT NULL,
    speaker TEXT NOT NULL,
    transcript TEXT NOT NULL,
    agent_name TEXT,
    function_called TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Token usage table (tracks API costs)
CREATE TABLE token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_session_id UUID REFERENCES call_sessions(id),
    model_name TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_per_input_token NUMERIC(10, 8),
    cost_per_output_token NUMERIC(10, 8),
    total_cost_usd NUMERIC(10, 4),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Call summaries table (AI-generated call summaries)
CREATE TABLE call_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_session_id UUID REFERENCES call_sessions(id) UNIQUE,
    summary_text TEXT NOT NULL,
    key_points TEXT[],
    action_items TEXT[],
    call_category TEXT,
    business_outcome TEXT,
    sales_value_usd NUMERIC(10, 2),
    generated_by TEXT DEFAULT 'gpt-4o',
    tokens_used INTEGER,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_call_sessions_agent_id ON call_sessions(agent_id);
CREATE INDEX idx_call_sessions_started_at ON call_sessions(started_at);
CREATE INDEX idx_conversation_turns_call_session_id ON conversation_turns(call_session_id);
CREATE INDEX idx_token_usage_call_session_id ON token_usage(call_session_id);
CREATE INDEX idx_call_summaries_call_session_id ON call_summaries(call_session_id);
```

## 🧪 Testing Locally

### Option 1: Run Voxie Agent Creator (Development Mode)

This starts the multi-agent system where Voxie helps create custom agents:

```bash
# Start Voxie in development mode (auto-joins new LiveKit rooms)
cd voxie-test
uv run python src/agent.py dev
```

**What this does:**
- Starts Voxie agent
- Auto-joins any new LiveKit rooms
- Guides users through creating custom voice agents
- Saves agents to database
- Generates call summaries for calls >3 minutes

**Test it:**
1. Create a LiveKit room using your LiveKit dashboard or API
2. Join the room with a client (web/mobile)
3. Speak with Voxie to create a custom agent
4. Test the created agent in demo mode

### Option 2: Run Specific Agent by ID

Load and run a pre-configured agent from the database:

```bash
# Set the agent ID you want to run
export AGENT_ID="your-agent-id-from-database"

# Start the specific agent in development mode
cd voxie-test
uv run python src/agent.py dev
```

### Option 3: Run Backend API Server

Start the FastAPI backend for dashboard and API access:

```bash
# Start backend server
python backend_server.py

# Server runs on http://localhost:8000
```

**Available Endpoints:**

- `GET /` - Health check
- `GET /api/agents` - List all agents
- `GET /api/agents/{agent_id}` - Get specific agent
- `PUT /api/agents/{agent_id}` - Update agent
- `DELETE /api/agents/{agent_id}` - Delete agent
- `GET /api/analytics/summary` - Get analytics summary
- `GET /api/analytics/recent-calls` - Get recent call history
- `GET /api/agents/create-stream/{session_id}` - SSE stream for real-time logs

**Test the API:**

```bash
# List all agents
curl http://localhost:8000/api/agents

# Get analytics summary
curl http://localhost:8000/api/analytics/summary

# Get recent calls
curl http://localhost:8000/api/analytics/recent-calls
```

### Option 4: Test with Dashboard Frontend

```bash
# Open the dashboard in your browser
open http://localhost:8000/dashboard
```

The dashboard allows you to:
- View all created agents
- View call analytics (from Voxie interactions)
- See call summaries and statistics

**Note:** To interact with Voxie and create agents, you'll need to connect through a LiveKit room using Option 1 or 2 above.

## 🏗️ Production Deployment

### Deploy Backend Server

#### Option A: Deploy to Cloud Platform (e.g., Railway, Render, Fly.io)

1. **Prepare for deployment:**

```bash
# Ensure all dependencies are in requirements files
uv pip freeze > requirements.txt
```

2. **Set environment variables** in your cloud platform:
   - All variables from `.env.local`
   - `PORT=8000` (or your platform's default)

3. **Deploy command:**

```bash
# Most platforms auto-detect and run:
python backend_server.py
```

4. **Update BACKEND_URL** in your production `.env`:

```bash
BACKEND_URL="https://your-backend-domain.com"
```

#### Option B: Deploy with Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements
COPY requirements.txt requirements-backend.txt ./

# Install dependencies
RUN uv pip install --system -r requirements.txt
RUN uv pip install --system -r requirements-backend.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run backend
CMD ["python", "backend_server.py"]
```

```bash
# Build and run
docker build -t voxie-backend .
docker run -p 8000:8000 --env-file .env.local voxie-backend
```

### Deploy Voice Agents

#### Development Mode

For development and testing, agents automatically connect when rooms are created:

```bash
# Run Voxie in development mode (auto-joins any new room)
cd voxie-test
uv run python src/agent.py dev
```

#### Production Mode (Single Process per Call)

For production deployments, you can manually run specific agents:

```bash
# Start a specific agent for a specific room
AGENT_ID="agent-id" ROOM_NAME="room-name" python simple_agent.py
```

#### Scaling Strategy

For high-traffic production:

1. **Deploy backend API** to cloud platform (handles HTTP requests & analytics)
2. **Deploy Voxie agents** to compute instances (handle voice interactions)
3. **Connect via LiveKit** rooms for real-time voice communication
4. **Auto-scale agent workers** based on active room count

Example architecture:

```
Frontend Dashboard → Backend API (Analytics & Agent CRUD)
                          ↓
                      Supabase DB (Agent configs & call data)

User → LiveKit Rooms → Voxie Agents (deployed separately)
```

**Note:** The dashboard is for viewing agent configurations and analytics only. Users interact with Voxie by joining LiveKit rooms directly.

## 📊 Database Analytics

### View Call Summaries

```bash
# Run analytics scripts
python -c "
import sys
sys.path.append('./function_call')
from supabase_client import supabase_client

# Get recent summaries
result = supabase_client.client.table('call_summaries')\
    .select('*')\
    .order('generated_at', desc=True)\
    .limit(5)\
    .execute()

for summary in result.data:
    print(f\"📞 {summary['call_category']}: {summary['business_outcome']}\")
    print(f\"   Summary: {summary['summary_text']}\")
    print()
"
```

### Check Call Statistics

```python
# check_calls.py
import sys
sys.path.append('./function_call')
from supabase_client import supabase_client

# Count all call sessions
all_calls = supabase_client.client.table('call_sessions').select('id', count='exact').execute()
print(f"📞 Total call sessions: {all_calls.count}")

# Count completed calls
completed = supabase_client.client.table('call_sessions').select('id', count='exact').eq('call_status', 'completed').execute()
print(f"✅ Completed calls: {completed.count}")

# Count summaries
summaries = supabase_client.client.table('call_summaries').select('id', count='exact').execute()
print(f"📝 Call summaries: {summaries.count}")
```

## 🔧 Troubleshooting

### Common Issues

**Issue: Agent not connecting to LiveKit**
```bash
# Check LiveKit credentials
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Test LiveKit connection
curl -X POST "$LIVEKIT_URL/twirp/livekit.RoomService/CreateRoom" \
  -H "Authorization: Bearer $(python -c 'from livekit import api; print(api.AccessToken(\"$LIVEKIT_API_KEY\", \"$LIVEKIT_API_SECRET\").to_jwt())')"
```

**Issue: Supabase connection fails**
```python
# Test Supabase connection
python -c "
import os
from supabase import create_client
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
print('✅ Supabase connected:', client.table('agents').select('id').limit(1).execute())
"
```

**Issue: OpenAI API errors**
```bash
# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Issue: Call summaries not generating**
- Summaries only generate for calls >3 minutes
- Check logs for GPT-4o API errors
- Verify OpenAI API key has GPT-4o access

### Enable Debug Logging

```python
# Add to top of agent.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📁 Project Structure

```
voxie-clean/
├── voxie-test/
│   └── src/
│       ├── agent.py                    # Main multi-agent system
│       ├── call_analytics.py           # Call tracking & analytics
│       ├── transcription_handler.py    # Transcription & summarization
│       ├── knowledge_base_tools.py     # Knowledge base integration
│       └── agent_persistence.py        # Agent storage/loading
├── function_call/
│   ├── supabase_client.py             # Supabase database client
│   └── agent_persistence.py           # Agent CRUD operations
├── backend_server.py                   # FastAPI REST API server
├── backend_log_handler.py             # Real-time log streaming
├── simple_agent.py                    # Production agent runner
├── .env.local                         # Environment configuration
├── requirements.txt                   # Python dependencies
├── requirements-backend.txt           # Backend dependencies
└── README.md                          # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Contact: [Your contact information]

## 🙏 Acknowledgments

- **LiveKit** - Real-time voice infrastructure
- **OpenAI** - GPT-4o for agent intelligence and summaries
- **Supabase** - Database and backend services
- **Deepgram** - Speech-to-text transcription
