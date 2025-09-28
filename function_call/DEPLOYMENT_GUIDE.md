# Production Deployment Guide

This guide explains how to deploy the WebSocket communication server to work with your existing LiveKit Cloud agent.

## Architecture Overview

```
LiveKit Cloud Agent (livestream-demo-jtpaw0s0.livekit.cloud)
    ↓ HTTP Webhooks
Railway WebSocket Server
    ↓ WebSocket Events
Frontend Applications
```

## 1. Deploy WebSocket Server to Railway

### Prerequisites
- Railway account: https://railway.app
- GitHub repository with this code

### Steps

1. **Connect GitHub Repository**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository containing this webhook server

2. **Configure Environment Variables**
   ```
   PORT=5000
   ENV=production
   WEBHOOK_SERVER_URL=https://your-railway-app.railway.app
   ```

3. **Deploy**
   - Railway will automatically detect the `railway.json` configuration
   - It will install dependencies from `requirements.txt`
   - Start command: `python webhook_server.py`
   - Health check: `/health` endpoint

4. **Get Deployment URL**
   - After deployment, Railway will provide a URL like:
   - `https://your-app-name.railway.app`

## 2. Update LiveKit Agent Configuration

### Add Production Bridge to LiveKit Agent

The LiveKit agent code has already been updated with production bridge integration. You need to:

1. **Set Environment Variable** in your LiveKit Cloud deployment:
   ```
   WEBHOOK_SERVER_URL=https://your-railway-app.railway.app
   ```

2. **Verify Integration**
   - The agent will automatically detect production mode
   - Events will be sent via HTTP to your Railway webhook server
   - Webhook server forwards events to WebSocket clients

## 3. Frontend Integration

### WebSocket Connection
```javascript
const socket = io('https://your-railway-app.railway.app');

// Listen for agent creation events
socket.on('agent_creation_update', (data) => {
    console.log('Agent creation step:', data);
    // Update UI based on step/status
});

// Start agent creation
socket.emit('start_agent_creation', {
    session_id: 'unique-session-id',
    requirements: {
        business_type: 'restaurant',
        business_name: 'Mario\'s Pizza'
    }
});
```

### Action-Based Events
The system emits specific action types for frontend tools:

```javascript
socket.on('action_event', (data) => {
    switch(data.action_type) {
        case 'database_creation':
            // Show DatabaseSetupTool component
            break;
        case 'knowledge_base_setup':
            // Show KnowledgeBaseConfigTool component
            break;
        case 'mcp_connection':
            // Show MCPConnectionTool component
            break;
        // ... other action types
    }
});
```

## 4. Testing the Integration

### 1. Test WebSocket Server Health
```bash
curl https://your-railway-app.railway.app/health
```

### 2. Test Voice Interaction
1. Connect to your LiveKit agent via voice
2. Say: "Create a restaurant agent for Mario's Pizza"
3. Check Railway logs for incoming webhook events
4. Verify WebSocket events are broadcast to connected clients

### 3. Test Direct Agent Creation
```bash
# Test agent-event endpoint
curl -X POST https://your-railway-app.railway.app/agent-event \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "step": "scenario",
    "status": "started",
    "message": "Analyzing business requirements..."
  }'
```

## 5. Monitoring and Logs

### Railway Logs
- View real-time logs in Railway dashboard
- Monitor webhook event reception
- Check WebSocket connection status

### LiveKit Agent Logs
- Production bridge events are logged in LiveKit Cloud
- Console logs show event transmission status

## 6. Security Considerations

### CORS Configuration
- WebSocket server allows all origins (`cors_allowed_origins="*"`)
- In production, restrict to your frontend domains

### Webhook Security
- Consider adding webhook signatures for production
- Validate incoming requests from LiveKit agent

## 7. Scaling

### Railway Auto-scaling
- Railway automatically scales based on traffic
- Monitor resource usage in Railway dashboard

### WebSocket Connections
- Current setup supports multiple concurrent sessions
- Each session has unique session_id for isolation

## Troubleshooting

### Common Issues

1. **Webhook Events Not Received**
   - Check WEBHOOK_SERVER_URL environment variable
   - Verify Railway deployment URL
   - Check LiveKit agent logs for HTTP errors

2. **WebSocket Connection Failed**
   - Verify Railway deployment is running
   - Check CORS configuration
   - Ensure WebSocket support is enabled

3. **Events Not Broadcasting**
   - Check if event_broadcaster is initialized
   - Verify session management in webhook_server.py
   - Monitor Railway logs for errors

### Debug Endpoints

- `/health` - Server health check
- `/analytics` - Search analytics (if applicable)
- Debug any specific query: `/debug/search/<query>`

## Summary

Your deployment architecture:

1. **LiveKit Cloud Agent** - Already deployed and running
2. **Railway WebSocket Server** - Receives webhooks, broadcasts WebSocket events
3. **Frontend Applications** - Connect via WebSocket for real-time updates

The production bridge automatically detects the environment and routes events appropriately:
- Production: HTTP webhooks → Railway server → WebSocket clients
- Development: Console logs + optional local WebSocket server