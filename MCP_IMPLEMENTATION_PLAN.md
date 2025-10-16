# MCP Integration Implementation Plan
## Model Context Protocol for Voxie Voice Agents

### Executive Summary

This document outlines the implementation plan for integrating **Model Context Protocol (MCP)** into the Voxie voice agent system, starting with **Zapier** and **Google Calendar** integrations.

MCP will enable Voxie agents to interact with external services seamlessly, allowing them to perform real-world actions like:
- Creating calendar appointments (Google Calendar)
- Triggering automations and workflows (Zapier)
- Connecting to 1000+ apps via Zapier

---

## 📚 Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Why MCP for Voxie?](#why-mcp-for-voxie)
3. [Architecture Overview](#architecture-overview)
4. [Zapier MCP Server Implementation](#zapier-mcp-server)
5. [Google Calendar MCP Server Implementation](#google-calendar-mcp-server)
6. [Integration with LiveKit Agents](#integration-with-livekit-agents)
7. [Implementation Phases](#implementation-phases)
8. [Code Structure](#code-structure)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Plan](#deployment-plan)
11. [Future Expansion](#future-expansion)

---

## What is MCP?

**Model Context Protocol (MCP)** is an open protocol created by Anthropic that enables AI applications to securely connect to external data sources and tools.

### Key Concepts

- **MCP Server**: Exposes tools/resources to AI applications
- **MCP Client**: Consumes tools from MCP servers (your Voxie agents)
- **Tools**: Functions the AI can call (e.g., "create_calendar_event")
- **Resources**: Data sources the AI can access (e.g., calendar list)
- **Prompts**: Templates for common operations

### MCP Benefits

✅ **Standardized**: One protocol for all integrations
✅ **Secure**: OAuth flows and credential management built-in
✅ **Composable**: Mix and match different MCP servers
✅ **Maintainable**: Official servers maintained by service providers
✅ **Scalable**: Add new integrations without changing agent code

---

## Why MCP for Voxie?

### Current State (Without MCP)

```python
# Each integration requires custom code in agent
@function_tool
async def create_calendar_event(self, date: str, time: str):
    # Custom Google Calendar API code here
    # OAuth handling, token refresh, error handling
    # All hardcoded in agent
    pass

@function_tool
async def trigger_zapier_webhook(self, data: dict):
    # Custom Zapier webhook code
    # Different pattern from calendar
    pass
```

❌ **Problems:**
- Code duplication across agents
- Hard to maintain (each integration is different)
- Credentials scattered everywhere
- Difficult to add new integrations
- No standardization

### Future State (With MCP)

```python
# Agents automatically get tools from MCP servers
# No custom integration code needed!

# Agent can now use:
# - calendar_create_event (from Google Calendar MCP)
# - zapier_trigger_zap (from Zapier MCP)
# - Any other MCP server you add
```

✅ **Benefits:**
- Centralized integration logic
- Standard OAuth handling
- Easy to add new services
- Maintained by service providers
- Credentials managed securely

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VOXIE SYSTEM                                 │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Voxie Agent  │       │ Spawned Agent │       │ Spawned Agent │
│  (Creator)    │       │   (Customer)  │       │  (Restaurant) │
└───────────────┘       └───────────────┘       └───────────────┘
        │                        │                        │
        │                        │                        │
        │   Uses MCP Client      │                        │
        └────────────────────────┴────────────────────────┘
                                 │
                    MCP Client Library
                    (in each agent)
                                 │
                                 │
        ┌────────────────────────┴────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  ZAPIER MCP   │       │ GOOGLE CAL    │       │  FUTURE MCP   │
│    SERVER     │       │  MCP SERVER   │       │   SERVERS     │
│               │       │               │       │               │
│ • Trigger Zap │       │ • List Events │       │ • Slack       │
│ • List Zaps   │       │ • Create Event│       │ • Gmail       │
│ • Run Action  │       │ • Update Event│       │ • Notion      │
│               │       │ • Delete Event│       │ • etc...      │
└───────────────┘       └───────────────┘       └───────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Zapier API   │       │ Google Cal    │       │  Other APIs   │
│               │       │     API       │       │               │
└───────────────┘       └───────────────┘       └───────────────┘
```

### Data Flow

1. **User speaks to agent**: "Schedule a meeting tomorrow at 2 PM"
2. **Agent decides to use tool**: Uses MCP client to call `calendar_create_event`
3. **MCP client routes to server**: Forwards request to Google Calendar MCP server
4. **MCP server executes**: Calls Google Calendar API with proper auth
5. **Response flows back**: Result returned to agent → agent responds to user

---

## Zapier MCP Server

### Overview

The Zapier MCP server enables agents to:
- Trigger Zaps (automations)
- Run specific Zapier actions
- Query Zap status
- Access 6000+ app integrations via Zapier

### Features to Implement

#### Phase 1: Core Features
- ✅ Trigger Zap by webhook
- ✅ List available Zaps
- ✅ Run specific action

#### Phase 2: Advanced Features
- ⬜ Check Zap run history
- ⬜ Enable/disable Zaps
- ⬜ Create new Zaps programmatically

### Tools Provided

```python
# Tools exposed by Zapier MCP server
{
    "tools": [
        {
            "name": "zapier_trigger_zap",
            "description": "Trigger a Zapier automation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "zap_id": {"type": "string"},
                    "payload": {"type": "object"}
                }
            }
        },
        {
            "name": "zapier_list_zaps",
            "description": "List all available Zaps",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "zapier_run_action",
            "description": "Run a specific Zapier action",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "params": {"type": "object"}
                }
            }
        }
    ]
}
```

### Implementation Details

**File Structure:**
```
mcp_servers/
└── zapier/
    ├── server.py              # Main MCP server
    ├── zapier_client.py       # Zapier API wrapper
    ├── auth.py                # OAuth handling
    ├── config.py              # Configuration
    ├── requirements.txt       # Dependencies
    └── README.md              # Documentation
```

**Key Dependencies:**
```
mcp>=0.1.0                    # MCP SDK
requests>=2.31.0              # HTTP client
python-dotenv>=1.0.0          # Environment
```

**Environment Variables:**
```bash
ZAPIER_API_KEY=your_zapier_api_key
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/...
MCP_SERVER_PORT=3001
```

**Example Implementation:**

```python
# mcp_servers/zapier/server.py
from mcp import Server, Tool
from zapier_client import ZapierClient

server = Server("zapier")
zapier = ZapierClient()

@server.tool()
async def zapier_trigger_zap(zap_id: str, payload: dict) -> dict:
    """
    Trigger a Zapier automation

    Args:
        zap_id: The unique identifier for the Zap
        payload: Data to send to the Zap

    Returns:
        Result of the Zap execution
    """
    try:
        result = await zapier.trigger_zap(zap_id, payload)
        return {
            "success": True,
            "zap_id": zap_id,
            "run_id": result.get("run_id"),
            "status": result.get("status")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@server.tool()
async def zapier_list_zaps() -> list:
    """List all available Zaps for this account"""
    zaps = await zapier.list_zaps()
    return [{
        "id": zap["id"],
        "name": zap["name"],
        "status": zap["status"]
    } for zap in zaps]

# Start server
if __name__ == "__main__":
    server.run(port=3001)
```

### Use Cases

**For Restaurant Agent:**
```
User: "I'd like to make a reservation for tomorrow at 7 PM"
Agent calls: zapier_trigger_zap(
    zap_id="reservation_notification",
    payload={
        "customer_name": "John Doe",
        "date": "2025-10-17",
        "time": "19:00",
        "party_size": 2
    }
)
→ Triggers Zap that:
  - Sends SMS to restaurant manager
  - Creates Google Sheets entry
  - Sends confirmation email to customer
```

**For Medical Agent:**
```
User: "Can you send my test results to my email?"
Agent calls: zapier_trigger_zap(
    zap_id="send_medical_records",
    payload={
        "patient_id": "12345",
        "document_type": "test_results",
        "email": "patient@example.com"
    }
)
→ Triggers Zap that:
  - Retrieves file from secure storage
  - Sends via encrypted email
  - Logs access in compliance system
```

---

## Google Calendar MCP Server

### Overview

The Google Calendar MCP server enables agents to:
- Create calendar events
- List upcoming events
- Update existing events
- Delete events
- Check availability

### Features to Implement

#### Phase 1: Core Features
- ✅ Create event
- ✅ List events
- ✅ Get event details
- ✅ Delete event

#### Phase 2: Advanced Features
- ⬜ Update event
- ⬜ Check availability
- ⬜ Add attendees
- ⬜ Set reminders
- ⬜ Recurring events

### Tools Provided

```python
{
    "tools": [
        {
            "name": "calendar_create_event",
            "description": "Create a new calendar event",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start": {"type": "string"},  # ISO 8601
                    "end": {"type": "string"},
                    "description": {"type": "string"},
                    "attendees": {"type": "array"}
                },
                "required": ["summary", "start", "end"]
            }
        },
        {
            "name": "calendar_list_events",
            "description": "List upcoming calendar events",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "number"},
                    "time_min": {"type": "string"},
                    "time_max": {"type": "string"}
                }
            }
        },
        {
            "name": "calendar_delete_event",
            "description": "Delete a calendar event",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"}
                },
                "required": ["event_id"]
            }
        },
        {
            "name": "calendar_check_availability",
            "description": "Check if a time slot is available",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "end": {"type": "string"}
                },
                "required": ["start", "end"]
            }
        }
    ]
}
```

### Implementation Details

**File Structure:**
```
mcp_servers/
└── google_calendar/
    ├── server.py              # Main MCP server
    ├── calendar_client.py     # Google Calendar API wrapper
    ├── auth.py                # OAuth 2.0 handling
    ├── config.py              # Configuration
    ├── credentials.json       # OAuth credentials (gitignored)
    ├── token.json            # User tokens (gitignored)
    ├── requirements.txt       # Dependencies
    └── README.md              # Documentation
```

**Key Dependencies:**
```
mcp>=0.1.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
python-dotenv>=1.0.0
```

**Environment Variables:**
```bash
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=./token.json
GOOGLE_CALENDAR_ID=primary
MCP_SERVER_PORT=3002
```

**Example Implementation:**

```python
# mcp_servers/google_calendar/server.py
from mcp import Server, Tool
from calendar_client import CalendarClient
from datetime import datetime, timedelta

server = Server("google-calendar")
calendar = CalendarClient()

@server.tool()
async def calendar_create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    attendees: list = None
) -> dict:
    """
    Create a new Google Calendar event

    Args:
        summary: Event title
        start: Start time (ISO 8601 format)
        end: End time (ISO 8601 format)
        description: Event description
        attendees: List of email addresses

    Returns:
        Created event details
    """
    try:
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end,
                'timeZone': 'America/Los_Angeles',
            },
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        created_event = await calendar.create_event(event)

        return {
            "success": True,
            "event_id": created_event['id'],
            "summary": created_event['summary'],
            "start": created_event['start']['dateTime'],
            "link": created_event.get('htmlLink')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@server.tool()
async def calendar_list_events(
    max_results: int = 10,
    time_min: str = None,
    time_max: str = None
) -> list:
    """List upcoming calendar events"""
    if not time_min:
        time_min = datetime.utcnow().isoformat() + 'Z'

    if not time_max:
        # Default to 1 week from now
        time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

    events = await calendar.list_events(
        time_min=time_min,
        time_max=time_max,
        max_results=max_results
    )

    return [{
        "id": event['id'],
        "summary": event.get('summary', 'No title'),
        "start": event['start'].get('dateTime', event['start'].get('date')),
        "end": event['end'].get('dateTime', event['end'].get('date'))
    } for event in events]

@server.tool()
async def calendar_check_availability(start: str, end: str) -> dict:
    """Check if a time slot is available"""
    events = await calendar.list_events(time_min=start, time_max=end)

    return {
        "available": len(events) == 0,
        "conflicting_events": len(events),
        "conflicts": [{
            "summary": event.get('summary'),
            "start": event['start'].get('dateTime')
        } for event in events]
    }

# Start server
if __name__ == "__main__":
    server.run(port=3002)
```

**OAuth Setup:**

```python
# mcp_servers/google_calendar/auth.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    """Get or create Google Calendar credentials"""
    creds = None

    # Token file stores user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds
```

### Use Cases

**For Dental Office Agent:**
```
User: "I need to schedule a cleaning appointment"
Agent: "When would you like to come in?"
User: "Next Tuesday at 2 PM"

Agent calls: calendar_check_availability(
    start="2025-10-21T14:00:00",
    end="2025-10-21T15:00:00"
)
→ Returns: {"available": true}

Agent calls: calendar_create_event(
    summary="Dental Cleaning - John Doe",
    start="2025-10-21T14:00:00",
    end="2025-10-21T15:00:00",
    description="Regular cleaning appointment",
    attendees=["patient@example.com"]
)
→ Event created, confirmation email sent

Agent: "Perfect! I've scheduled your cleaning for Tuesday, October 21st at 2 PM. You'll receive a confirmation email shortly."
```

**For Business Agent:**
```
User: "What meetings do I have this week?"

Agent calls: calendar_list_events(
    max_results=20,
    time_min="2025-10-14T00:00:00Z",
    time_max="2025-10-20T23:59:59Z"
)

Agent: "You have 5 meetings this week:
1. Team standup - Monday 9 AM
2. Client call - Tuesday 2 PM
3. Project review - Wednesday 10 AM
4. Budget meeting - Thursday 3 PM
5. All hands - Friday 11 AM"
```

---

## Integration with LiveKit Agents

### Adding MCP to Voxie Agents

**Current Agent (Without MCP):**
```python
class RestaurantDemoAgent(Agent):
    def __init__(self):
        super().__init__(instructions=spec.instructions)

    @function_tool
    async def take_reservation(self, date, time, party_size, name):
        # Manual implementation
        return "Reservation confirmed"
```

**Enhanced Agent (With MCP):**
```python
from mcp_client import MCPClient

class RestaurantDemoAgent(Agent):
    def __init__(self):
        super().__init__(instructions=spec.instructions)

        # Initialize MCP clients
        self.mcp_calendar = MCPClient("http://localhost:3002")  # Google Calendar
        self.mcp_zapier = MCPClient("http://localhost:3001")    # Zapier

        # Load tools from MCP servers
        self.load_mcp_tools()

    async def load_mcp_tools(self):
        """Dynamically load tools from MCP servers"""
        # Get tools from Google Calendar MCP
        calendar_tools = await self.mcp_calendar.list_tools()

        # Get tools from Zapier MCP
        zapier_tools = await self.mcp_zapier.list_tools()

        # Register as function tools
        for tool in calendar_tools:
            self.register_tool(tool)

        for tool in zapier_tools:
            self.register_tool(tool)

    @function_tool
    async def take_reservation(self, date, time, party_size, name, phone):
        """Take a restaurant reservation using MCP"""

        # 1. Check calendar availability
        start_time = f"{date}T{time}:00"
        end_time = f"{date}T{time.split(':')[0]}:{int(time.split(':')[1]) + 60:02d}:00"

        availability = await self.mcp_calendar.call_tool(
            "calendar_check_availability",
            start=start_time,
            end=end_time
        )

        if not availability["available"]:
            return "Sorry, that time slot is not available. Would you like to try a different time?"

        # 2. Create calendar event
        event = await self.mcp_calendar.call_tool(
            "calendar_create_event",
            summary=f"Reservation: {name} - Party of {party_size}",
            start=start_time,
            end=end_time,
            description=f"Phone: {phone}\nParty size: {party_size}"
        )

        # 3. Trigger Zapier notification
        await self.mcp_zapier.call_tool(
            "zapier_trigger_zap",
            zap_id="restaurant_reservation",
            payload={
                "name": name,
                "phone": phone,
                "date": date,
                "time": time,
                "party_size": party_size,
                "calendar_link": event.get("link")
            }
        )

        return f"Perfect! I've reserved a table for {party_size} on {date} at {time} under the name {name}. You'll receive a confirmation text shortly."
```

### MCP Client Implementation

```python
# voxie-test/src/mcp_client.py
import aiohttp
import logging

logger = logging.getLogger("mcp-client")

class MCPClient:
    """Client for communicating with MCP servers"""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools_cache = None

    async def list_tools(self) -> list:
        """Get list of available tools from MCP server"""
        if self.tools_cache:
            return self.tools_cache

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/tools") as resp:
                result = await resp.json()
                self.tools_cache = result.get("tools", [])
                return self.tools_cache

    async def call_tool(self, tool_name: str, **params) -> dict:
        """Call a tool on the MCP server"""
        logger.info(f"🔧 Calling MCP tool: {tool_name}")
        logger.debug(f"   Params: {params}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/tools/{tool_name}",
                json=params
            ) as resp:
                result = await resp.json()
                logger.info(f"✅ MCP tool response: {result.get('success', False)}")
                return result

    async def get_resources(self) -> list:
        """Get available resources from MCP server"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.server_url}/resources") as resp:
                result = await resp.json()
                return result.get("resources", [])
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goals:**
- Set up MCP server infrastructure
- Implement basic Zapier integration
- Implement basic Google Calendar integration

**Tasks:**
1. Create `mcp_servers/` directory structure
2. Implement Zapier MCP server (basic trigger)
3. Implement Google Calendar MCP server (create event, list events)
4. Set up OAuth for Google Calendar
5. Create MCP client library
6. Write unit tests

**Deliverables:**
- Working Zapier MCP server
- Working Google Calendar MCP server
- MCP client library
- Documentation

### Phase 2: Agent Integration (Week 2)

**Goals:**
- Integrate MCP into existing agents
- Update agent factory to support MCP
- Test with real scenarios

**Tasks:**
1. Update `DynamicAgentFactory` to include MCP client
2. Modify restaurant agent to use calendar MCP
3. Modify medical agent to use calendar MCP
4. Add Zapier triggers to business workflows
5. Update agent instructions to mention new capabilities
6. Integration testing

**Deliverables:**
- Agents using MCP tools
- Updated agent prompts
- Integration tests
- User documentation

### Phase 3: Dashboard & Management (Week 3)

**Goals:**
- Add MCP management to dashboard
- Allow users to configure integrations
- Monitor MCP usage

**Tasks:**
1. Add MCP settings to agent dashboard
2. Create OAuth flow for Google Calendar in dashboard
3. Add Zapier webhook configuration UI
4. Display MCP tool usage in analytics
5. Add troubleshooting tools

**Deliverables:**
- Dashboard MCP settings page
- OAuth integration UI
- Analytics for MCP usage
- Admin tools

### Phase 4: Advanced Features (Week 4)

**Goals:**
- Add more MCP tools
- Implement error handling
- Optimize performance

**Tasks:**
1. Add calendar update/delete features
2. Add Zapier action querying
3. Implement retry logic
4. Add caching for MCP calls
5. Performance optimization
6. Load testing

**Deliverables:**
- Complete tool set
- Robust error handling
- Performance benchmarks
- Production readiness

---

## Code Structure

```
voxie-clean/
├── mcp_servers/                    # MCP server implementations
│   ├── zapier/
│   │   ├── server.py              # Zapier MCP server
│   │   ├── zapier_client.py       # Zapier API wrapper
│   │   ├── auth.py                # Authentication
│   │   ├── config.py              # Configuration
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   ├── google_calendar/
│   │   ├── server.py              # Google Calendar MCP server
│   │   ├── calendar_client.py     # Google Calendar API wrapper
│   │   ├── auth.py                # OAuth 2.0 handling
│   │   ├── config.py              # Configuration
│   │   ├── credentials.json       # OAuth credentials (gitignored)
│   │   ├── token.json            # User tokens (gitignored)
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   └── shared/                     # Shared utilities
│       ├── base_server.py         # Base MCP server class
│       ├── auth_helpers.py        # Common auth functions
│       └── utils.py               # Utilities
│
├── voxie-test/src/
│   ├── mcp_client.py              # MCP client for agents
│   ├── mcp_integration.py         # Integration helpers
│   └── agent.py                   # Updated with MCP support
│
├── spawner/
│   ├── spawner_agent.py           # Updated with MCP support
│   └── dynamic_agent_factory.py   # Updated to include MCP
│
├── backend_server.py              # Add MCP management endpoints
│
└── MCP_IMPLEMENTATION_GUIDE.md    # This document
```

---

## Testing Strategy

### Unit Tests

```python
# tests/mcp_servers/test_zapier.py
import pytest
from mcp_servers.zapier.server import zapier_trigger_zap

@pytest.mark.asyncio
async def test_trigger_zap_success():
    result = await zapier_trigger_zap(
        zap_id="test_zap_123",
        payload={"test": "data"}
    )
    assert result["success"] == True
    assert "run_id" in result

@pytest.mark.asyncio
async def test_trigger_zap_invalid_id():
    result = await zapier_trigger_zap(
        zap_id="invalid",
        payload={}
    )
    assert result["success"] == False
    assert "error" in result
```

### Integration Tests

```python
# tests/integration/test_mcp_agent.py
import pytest
from mcp_client import MCPClient
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_agent_creates_calendar_event():
    # Start MCP servers
    calendar_server = await start_calendar_server()

    # Create MCP client
    client = MCPClient("http://localhost:3002")

    # Create event
    tomorrow = datetime.now() + timedelta(days=1)
    result = await client.call_tool(
        "calendar_create_event",
        summary="Test Appointment",
        start=tomorrow.isoformat(),
        end=(tomorrow + timedelta(hours=1)).isoformat()
    )

    assert result["success"] == True
    assert "event_id" in result

    # Cleanup
    await calendar_server.stop()
```

### End-to-End Tests

```python
# tests/e2e/test_reservation_flow.py
@pytest.mark.asyncio
async def test_full_reservation_flow():
    """Test complete reservation from user speech to calendar event"""

    # 1. Start all services
    await start_mcp_servers()
    await start_livekit_agent()

    # 2. Simulate user conversation
    user_input = "I'd like to make a reservation for tomorrow at 7 PM for 4 people"

    # 3. Agent processes and uses MCP
    response = await agent.process_input(user_input)

    # 4. Verify calendar event created
    events = await calendar_client.list_events()
    assert len(events) > 0
    assert "4 people" in events[0]["description"]

    # 5. Verify Zapier triggered
    zap_runs = await zapier_client.get_recent_runs()
    assert len(zap_runs) > 0
```

---

## Deployment Plan

### Development Environment

```bash
# Terminal 1: Google Calendar MCP Server
cd mcp_servers/google_calendar
python server.py

# Terminal 2: Zapier MCP Server
cd mcp_servers/zapier
python server.py

# Terminal 3: Voxie Agent (with MCP)
cd voxie-test
python src/agent.py

# Terminal 4: Spawner (with MCP)
cd spawner
python spawner_agent.py

# Terminal 5: Backend API
python backend_server.py
```

### Production Deployment (Docker Compose)

```yaml
# docker-compose.mcp.yml
version: '3.8'

services:
  # MCP Servers
  mcp-calendar:
    build: ./mcp_servers/google_calendar
    environment:
      - GOOGLE_CALENDAR_CREDENTIALS_PATH=/app/credentials.json
      - MCP_SERVER_PORT=3002
    volumes:
      - ./secrets/google_calendar:/app/secrets
    ports:
      - "3002:3002"
    restart: unless-stopped

  mcp-zapier:
    build: ./mcp_servers/zapier
    environment:
      - ZAPIER_API_KEY=${ZAPIER_API_KEY}
      - MCP_SERVER_PORT=3001
    ports:
      - "3001:3001"
    restart: unless-stopped

  # Voxie Agent (with MCP)
  voxie:
    build: ./voxie-test
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - MCP_CALENDAR_URL=http://mcp-calendar:3002
      - MCP_ZAPIER_URL=http://mcp-zapier:3001
    depends_on:
      - mcp-calendar
      - mcp-zapier

  # Spawner (with MCP)
  spawner:
    build: ./spawner
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL_SPAWNER}
      - MCP_CALENDAR_URL=http://mcp-calendar:3002
      - MCP_ZAPIER_URL=http://mcp-zapier:3001
    depends_on:
      - mcp-calendar
      - mcp-zapier
    deploy:
      replicas: 3

  # Backend API
  backend:
    build: .
    environment:
      - MCP_CALENDAR_URL=http://mcp-calendar:3002
      - MCP_ZAPIER_URL=http://mcp-zapier:3001
    ports:
      - "8000:8000"
    depends_on:
      - mcp-calendar
      - mcp-zapier
```

### Environment Variables

```bash
# .env.mcp
# Google Calendar MCP
GOOGLE_CALENDAR_CREDENTIALS_PATH=./secrets/google_credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=./secrets/google_token.json
GOOGLE_CALENDAR_ID=primary

# Zapier MCP
ZAPIER_API_KEY=your_zapier_api_key
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/...

# MCP Server URLs (for agents)
MCP_CALENDAR_URL=http://localhost:3002
MCP_ZAPIER_URL=http://localhost:3001
```

---

## Future Expansion

### Additional MCP Servers to Add

1. **Slack MCP**
   - Send messages
   - Create channels
   - Upload files
   - Search history

2. **Gmail MCP**
   - Send emails
   - Read inbox
   - Search emails
   - Manage labels

3. **Notion MCP**
   - Create pages
   - Update databases
   - Search content
   - Manage tasks

4. **Stripe MCP**
   - Process payments
   - Create invoices
   - Manage subscriptions
   - View transactions

5. **Twilio MCP**
   - Send SMS
   - Make calls
   - Check call logs
   - Manage phone numbers

6. **Shopify MCP**
   - Manage orders
   - Update inventory
   - Create products
   - Process refunds

7. **HubSpot MCP**
   - Manage contacts
   - Create deals
   - Track emails
   - Update CRM

8. **Salesforce MCP**
   - Manage leads
   - Update opportunities
   - Create tasks
   - Run reports

### Ecosystem Benefits

Once MCP infrastructure is in place:
- ✅ Add new integration in ~1 hour (vs. ~1 week before)
- ✅ No agent code changes needed
- ✅ Centralized credential management
- ✅ Standard error handling
- ✅ Automatic retry logic
- ✅ Built-in logging and monitoring

---

## Getting Started Checklist

### Before Implementation

- [ ] Review MCP specification at https://modelcontextprotocol.io
- [ ] Set up Zapier account and API key
- [ ] Set up Google Cloud project for Calendar API
- [ ] Create OAuth credentials for Google Calendar
- [ ] Decide on MCP server hosting (local vs. cloud)
- [ ] Review security implications

### Phase 1 Setup

- [ ] Create `mcp_servers/` directory
- [ ] Install MCP SDK: `pip install mcp`
- [ ] Set up Google Calendar OAuth
- [ ] Get Zapier API key
- [ ] Implement basic Zapier MCP server
- [ ] Implement basic Google Calendar MCP server
- [ ] Test both servers independently

### Phase 2 Integration

- [ ] Create `mcp_client.py` in voxie-test/src
- [ ] Update one agent to use MCP (start with restaurant)
- [ ] Test agent with MCP tools
- [ ] Roll out to other agents
- [ ] Update spawner to support MCP

### Phase 3 Production

- [ ] Set up production MCP servers
- [ ] Configure OAuth for production
- [ ] Add monitoring and logging
- [ ] Deploy with Docker Compose
- [ ] Test end-to-end flows
- [ ] Document for users

---

## Summary

MCP integration will transform Voxie from a voice agent platform into a **complete automation platform** where agents can:

- 📅 **Manage calendars** (Google Calendar)
- ⚡ **Trigger workflows** (Zapier → 6000+ apps)
- 📧 **Send emails** (Gmail - future)
- 💬 **Send messages** (Slack - future)
- 💳 **Process payments** (Stripe - future)
- 🛍️ **Manage orders** (Shopify - future)

**Key Benefits:**
1. **Standardized**: One pattern for all integrations
2. **Scalable**: Easy to add new services
3. **Maintainable**: Centralized logic
4. **Secure**: Built-in OAuth and credential management
5. **Future-proof**: Industry standard protocol

**Timeline:** 4 weeks to full implementation
**Effort:** ~80 hours total
**Complexity:** Medium (OAuth is the hardest part)

Ready to implement! 🚀
