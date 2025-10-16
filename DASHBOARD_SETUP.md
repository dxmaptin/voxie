# Agent Dashboard Setup Guide

## Overview
A comprehensive dashboard to view, edit, and manage all your AI voice agents stored in Supabase.

## Features
- View all agents from Supabase database
- Real-time statistics (Total, Active, Draft agents)
- Edit agent configurations (name, prompt, voice, status, etc.)
- Delete agents with confirmation
- View detailed agent information including JSON data
- Beautiful, responsive UI
- Full CRUD API backend

## Quick Start

### 1. Start the Backend Server

```bash
python backend_server.py
```

The server will run on `http://localhost:8000`

### 2. Open the Dashboard

Simply open `agent_dashboard.html` in your browser:

```bash
open agent_dashboard.html
```

Or serve it via a local server:

```bash
python -m http.server 8001
# Then visit http://localhost:8001/agent_dashboard.html
```

### 3. The Dashboard Will:
- Automatically connect to your local backend
- Fetch all agents from Supabase
- Display statistics and agent cards
- Allow you to edit/delete agents

## Backend API Endpoints

All endpoints run on `http://localhost:8000`:

### GET `/api/agents`
List all agents from database
```bash
curl http://localhost:8000/api/agents
```

### GET `/api/agents/{agent_id}`
Get specific agent by ID
```bash
curl http://localhost:8000/api/agents/{agent_id}
```

### PUT `/api/agents/{agent_id}`
Update an agent (partial updates supported)
```bash
curl -X PUT http://localhost:8000/api/agents/{agent_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "status": "active"}'
```

### DELETE `/api/agents/{agent_id}`
Delete an agent
```bash
curl -X DELETE http://localhost:8000/api/agents/{agent_id}
```

## Dashboard Features

### Agent Cards
Each card shows:
- Agent name and tagline
- Avatar image
- Category badge
- Voice and model info
- Status and creation date
- Truncated prompt preview
- Edit and Delete buttons

### Edit Modal
Allows editing:
- Agent name
- Tagline
- Category
- Voice (alloy, echo, fable, onyx, nova, shimmer)
- Status (draft, active, archived)
- Prompt text
- Avatar URL

### Details Modal
Shows complete JSON data:
- Prompt variables
- Provider config
- Settings
- All metadata

### Statistics Dashboard
- Total Agents
- Active Agents
- Draft Agents

## Connecting Your Frontend

To integrate this with your own frontend:

```javascript
const API_BASE = 'http://localhost:8000';

// List all agents
const response = await fetch(`${API_BASE}/api/agents`);
const data = await response.json();
console.log(data.agents);

// Get specific agent
const agent = await fetch(`${API_BASE}/api/agents/${agentId}`);

// Update agent
await fetch(`${API_BASE}/api/agents/${agentId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'New Name', status: 'active' })
});

// Delete agent
await fetch(`${API_BASE}/api/agents/${agentId}`, { method: 'DELETE' });
```

## Database Schema

The dashboard works with this Supabase `agents` table structure:

```
- id (uuid)
- name (text)
- avatar_url (text)
- tagline (text)
- category (text)
- language (text[])
- prompt_source (text)
- prompt_text (text)
- prompt_variables (jsonb)
- voice (text)
- model (text)
- provider (text)
- provider_config (jsonb)
- settings (jsonb)
- status (text)
- status_type (text)
- visibility (text)
- access_mode (text)
- created_at (timestamp)
- updated_at (timestamp)
```

## Environment Requirements

Make sure your `.env.local` has:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

## Troubleshooting

### CORS Issues
If you get CORS errors:
- The backend is configured with `allow_origins=["*"]` for development
- For production, update `backend_server.py` to specify your frontend domain

### Connection Failed
1. Make sure `backend_server.py` is running on port 8000
2. Check that Supabase credentials are in `.env.local`
3. Verify the Supabase `agents` table exists

### No Agents Showing
1. Check browser console for errors
2. Verify agents exist in Supabase
3. Test the API directly: `curl http://localhost:8000/api/agents`

## Next Steps

- Deploy backend to production server
- Update `API_BASE` in dashboard HTML to production URL
- Add authentication/authorization
- Add agent creation flow to dashboard
- Add search and filter functionality
