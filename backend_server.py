"""
FastAPI Backend Server for Voxie Agent Creation with SSE
Provides real-time logging stream during agent creation
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from fastapi.staticfiles import StaticFiles
# Load environment variables from .env.local (local) or .env (cloud)
from dotenv import load_dotenv

# Try .env.local first (local development), then .env (cloud deployment)
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
    print("✅ Loaded environment from .env.local")
elif os.path.exists('.env'):
    load_dotenv('.env')
    print("✅ Loaded environment from .env")
else:
    print("⚠️ No .env file found, using system environment variables")

# Setup logger
logger = logging.getLogger("voxie-backend")

# Event bus for broadcasting agent creation events
class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, asyncio.Queue] = {}
        self.event_buffer: Dict[str, list] = {}  # Store recent events
        self.max_buffer_size = 100  # Keep last 100 events per session

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific session"""
        queue = asyncio.Queue()
        self.subscribers[session_id] = queue

        # Send buffered events to new subscriber
        if session_id in self.event_buffer:
            for event in self.event_buffer[session_id]:
                asyncio.create_task(queue.put(event))

        return queue

    def unsubscribe(self, session_id: str):
        """Unsubscribe from events"""
        if session_id in self.subscribers:
            del self.subscribers[session_id]

    async def publish(self, session_id: str, event: Dict[str, Any]):
        """Publish an event to subscribers and buffer it"""
        # Add to buffer
        if session_id not in self.event_buffer:
            self.event_buffer[session_id] = []

        self.event_buffer[session_id].append(event)

        # Limit buffer size
        if len(self.event_buffer[session_id]) > self.max_buffer_size:
            self.event_buffer[session_id].pop(0)

        # Send to active subscribers
        if session_id in self.subscribers:
            await self.subscribers[session_id].put(event)

# Global event bus
event_bus = EventBus()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logging.info("🚀 Backend server starting...")
    yield
    logging.info("🔒 Backend server shutting down...")

app = FastAPI(title="Voxie Backend API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AgentCreationRequest(BaseModel):
    business_name: str
    business_type: str
    requirements: Optional[Dict[str, Any]] = None

class AgentCreationResponse(BaseModel):
    session_id: str
    message: str

# SSE Event Formatter
def format_sse(data: dict, event: Optional[str] = None) -> str:
    """Format data as SSE message"""
    msg = ""
    if event:
        msg += f"event: {event}\n"
    msg += f"data: {json.dumps(data)}\n\n"
    return msg

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "voxie-backend",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/agents/create", response_model=AgentCreationResponse)
async def create_agent(request: AgentCreationRequest):
    """
    Initiate agent creation (non-streaming)
    Returns session_id for tracking
    """
    import uuid
    session_id = str(uuid.uuid4())

    # This would trigger your actual agent creation logic
    # For now, we'll just return the session ID

    return AgentCreationResponse(
        session_id=session_id,
        message="Agent creation initiated. Use /api/agents/create-stream for real-time updates."
    )

@app.get("/api/agents/create-stream/{session_id}")
async def create_agent_stream(session_id: str):
    """
    Stream agent creation progress via Server-Sent Events (SSE)

    Example usage from frontend:
    ```javascript
    const eventSource = new EventSource(`/api/agents/create-stream/${sessionId}`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data.message);
    };
    ```
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        # Subscribe to events for this session
        queue = event_bus.subscribe(session_id)

        try:
            # Send initial connection message
            yield format_sse({
                "status": "connected",
                "message": "🔗 Connected to agent creation stream",
                "timestamp": datetime.utcnow().isoformat()
            })

            # Stream events from the queue
            while True:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield format_sse(event)

                    # If this is a completion event, close the stream
                    if event.get("status") == "completed":
                        break

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield format_sse({
                        "status": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    })

        except asyncio.CancelledError:
            logging.info(f"Stream cancelled for session: {session_id}")
        finally:
            # Cleanup
            event_bus.unsubscribe(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.post("/api/agents/{session_id}/log")
async def log_event(session_id: str, event: Dict[str, Any]):
    """
    Internal endpoint for logging events during agent creation
    Called by your voice agent code
    """
    await event_bus.publish(session_id, event)
    return {"status": "ok"}

# ============= AGENT DASHBOARD CRUD ENDPOINTS =============

@app.get("/api/agents")
async def list_all_agents():
    """
    Get all agents from database
    Returns complete agent data for dashboard display
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client

        response = supabase_client.client.table('agents').select('*').order('created_at', desc=True).execute()

        return {
            "status": "success",
            "count": len(response.data) if response.data else 0,
            "agents": response.data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agents: {str(e)}")

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get a specific agent by ID
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client

        response = supabase_client.client.table('agents').select('*').eq('id', agent_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "status": "success",
            "agent": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agent: {str(e)}")

@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, updates: Dict[str, Any]):
    """
    Update an existing agent
    Accepts partial updates - only specified fields will be updated
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client

        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        response = supabase_client.client.table('agents').update(updates).eq('id', agent_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "status": "success",
            "message": "Agent updated successfully",
            "agent": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """
    Delete an agent by ID
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client

        response = supabase_client.client.table('agents').delete().eq('id', agent_id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "status": "success",
            "message": "Agent deleted successfully",
            "deleted_agent_id": agent_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting agent: {str(e)}")

# Helper function to publish events from your agent code
async def publish_log_event(session_id: str, status: str, message: str, **extra_data):
    """
    Helper function to publish log events
    Import this in your agent.py and call it during agent creation
    """
    import aiohttp

    event = {
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        **extra_data
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:8000/api/agents/{session_id}/log",
                json=event
            ) as resp:
                return await resp.json()
    except Exception as e:
        logging.error(f"Failed to publish event: {e}")
        return None


# ============= ANALYTICS API ENDPOINTS =============

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """
    Get summary analytics for dashboard
    """
    try:
        import sys
        sys.path.append('./function_call')
        sys.path.append('./voxie-test/src')
        from supabase_client import supabase_client

        # Get today's calls
        today = datetime.now(timezone.utc).date()

        # Total calls today
        calls_response = supabase_client.client.table('call_sessions')\
            .select('id, call_rating')\
            .gte('started_at', today.isoformat())\
            .execute()

        total_calls = len(calls_response.data) if calls_response.data else 0

        # Calculate average rating
        ratings = [c['call_rating'] for c in calls_response.data if c.get('call_rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Total cost today
        if calls_response.data:
            call_ids = [c['id'] for c in calls_response.data]
            tokens_response = supabase_client.client.table('token_usage')\
                .select('total_cost_usd')\
                .in_('call_session_id', call_ids)\
                .execute()

            total_cost = sum(t['total_cost_usd'] for t in tokens_response.data) if tokens_response.data else 0
        else:
            total_cost = 0

        # Active calls
        active_response = supabase_client.client.table('call_sessions')\
            .select('id')\
            .eq('call_status', 'active')\
            .execute()

        active_calls = len(active_response.data) if active_response.data else 0

        return {
            "status": "success",
            "total_calls": total_calls,
            "total_cost": total_cost,
            "avg_rating": avg_rating,
            "active_calls": active_calls
        }

    except Exception as e:
        logging.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@app.get("/api/analytics/recent-calls")
async def get_recent_calls(limit: int = 10):
    """
    Get recent calls for dashboard
    """
    try:
        import sys
        sys.path.append('./function_call')
        sys.path.append('./voxie-test/src')
        from supabase_client import supabase_client

        response = supabase_client.client.table('call_sessions')\
            .select('*')\
            .order('started_at', desc=True)\
            .limit(limit)\
            .execute()

        return {
            "status": "success",
            "calls": response.data or []
        }

    except Exception as e:
        logging.error(f"Failed to get recent calls: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent calls: {str(e)}")


# ============= CALL API ENDPOINTS (Exercise 2) =============

class CallStartRequest(BaseModel):
    agent_id: str
    customer_phone: Optional[str] = None

class CallStartResponse(BaseModel):
    status: str
    room_name: str
    token: str
    livekit_url: str
    agent_name: str

class CallEndRequest(BaseModel):
    room_name: str
    session_id: Optional[str] = None

@app.post("/api/call/start", response_model=CallStartResponse)
async def start_call(request: CallStartRequest):
    """
    Start a new call session with a specific agent
    - Creates a LiveKit room
    - Generates a client access token
    - Starts the agent process in the background
    - Returns connection details for the browser client
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client
        from livekit import api

        # Get agent from database
        agent_response = supabase_client.client.table('agents').select('*').eq('id', request.agent_id).execute()

        if not agent_response.data or len(agent_response.data) == 0:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")

        agent = agent_response.data[0]

        # Generate unique room name
        room_name = f"call_{request.agent_id[:8]}_{uuid.uuid4().hex[:8]}"

        # Get LiveKit configuration
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, livekit_api_key, livekit_api_secret]):
            raise HTTPException(status_code=500, detail="LiveKit configuration missing in environment")

        # Generate client access token
        token = api.AccessToken(livekit_api_key, livekit_api_secret)
        token.with_identity(f"user_{uuid.uuid4().hex[:8]}")
        token.with_name("Browser Client")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True
        ))

        client_token = token.to_jwt()

        # Start agent process in background
        # The agent will connect to the room and start listening
        logger.info(f"🚀 Starting agent {request.agent_id} for room {room_name}")

        # Launch agent process using simple_agent.py in production mode
        import subprocess

        env = os.environ.copy()
        env['AGENT_ID'] = request.agent_id
        env['ROOM_NAME'] = room_name

        # Create log file for this agent instance
        log_file_path = f"agent_logs/agent_{request.agent_id[:8]}_{room_name}.log"
        os.makedirs("agent_logs", exist_ok=True)

        # Use the voxie-test virtual environment's Python
        voxie_test_python = os.path.join(os.path.dirname(__file__), 'voxie-test', '.venv', 'bin', 'python3')

        # Start agent process in background (non-blocking)
        log_file = open(log_file_path, 'w')
        process = subprocess.Popen(
            [voxie_test_python, 'simple_agent.py'],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            start_new_session=True  # Detach from parent process
        )

        logger.info(f"✅ Agent process started (PID: {process.pid}) for room: {room_name}")
        logger.info(f"📝 Agent logs: {log_file_path}")

        # Quick check if process is still running after brief delay
        await asyncio.sleep(0.5)
        if process.poll() is not None:
            # Process has already exited
            logger.error(f"❌ Agent process exited immediately with code: {process.returncode}")
            logger.error(f"📝 Check logs at: {log_file_path}")
            raise HTTPException(status_code=500, detail=f"Agent process failed to start. Check logs at {log_file_path}")

        # Log to Supabase (optional - for tracking)
        try:
            session_id = str(uuid.uuid4())
            supabase_client.client.table('call_sessions').insert({
                'session_id': session_id,  # Generated UUID to satisfy not-null constraint
                'room_name': room_name,
                'agent_id': request.agent_id,
                'customer_phone': request.customer_phone or None,
                'call_status': 'active',
                'started_at': datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as log_error:
            logger.warning(f"Failed to log call session: {log_error}")

        return CallStartResponse(
            status="success",
            room_name=room_name,
            token=client_token,
            livekit_url=livekit_url,
            agent_name=agent.get('name', 'Agent')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start call: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start call: {str(e)}")


@app.post("/api/call/end")
async def end_call(request: CallEndRequest):
    """
    End a call session
    - Marks the call as completed in the database
    - The agent process will automatically exit when the room becomes empty
    """
    try:
        import sys
        sys.path.append('./function_call')
        from supabase_client import supabase_client

        # Update call session status
        try:
            supabase_client.client.table('call_sessions')\
                .update({
                    'call_status': 'completed',
                    'ended_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq('room_name', request.room_name)\
                .execute()

            logger.info(f"✅ Call ended for room: {request.room_name}")
        except Exception as log_error:
            logger.warning(f"Failed to update call session: {log_error}")

        return {
            "status": "success",
            "message": "Call ended successfully",
            "room_name": request.room_name
        }

    except Exception as e:
        logger.error(f"Failed to end call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end call: {str(e)}")


@app.get("/dashboard")
async def serve_dashboard():
    """
    Serve the dashboard HTML
    """
    return FileResponse("agent_dashboard.html")


@app.get("/call")
async def serve_call_interface():
    """
    Serve the simple call interface HTML (Exercise 2)
    """
    return FileResponse("simple_call_interface.html")

app.mount("/static", StaticFiles(directory="."), name="static")
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
