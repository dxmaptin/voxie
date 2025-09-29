from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import sys
from datetime import datetime
import uuid
import asyncio

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from voice_agent_function import function_call
    print("✅ Successfully imported voice_agent_function")
except ImportError as e:
    print(f"❌ Error importing voice_agent_function: {e}")
    print("Make sure voice_agent_function.py is in the same directory")
    sys.exit(1)

# Initialize Flask app and SocketIO
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

search_history = []

# Import and initialize event broadcaster and agent integration
event_broadcaster = None
agent_integrator = None

try:
    from event_broadcaster import initialize_broadcaster
    event_broadcaster = initialize_broadcaster(socketio)
    print("✅ Event broadcaster initialized")

    # Only initialize agent integrator if not running under Gunicorn
    # LiveKit agents require main thread registration
    if not os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn'):
        from agent_integration import initialize_agent_integrator
        agent_integrator = initialize_agent_integrator(event_broadcaster)
        print("✅ Agent integrator initialized")
    else:
        print("⚠️ Agent integrator disabled for Gunicorn (production mode)")

except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    event_broadcaster = None
    agent_integrator = None

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'client_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 Client disconnected: {request.sid}")
    if event_broadcaster:
        # Clean up any sessions associated with this client
        for session_id, session_data in list(event_broadcaster.active_sessions.items()):
            if session_data.get('client_id') == request.sid:
                event_broadcaster.disconnect_session(session_id)

@socketio.on('start_agent_creation')
def handle_start_agent_creation(data):
    """Handle agent creation start request from frontend"""
    try:
        session_id = data.get('session_id', str(uuid.uuid4()))
        requirements = data.get('requirements', {})

        print(f"🚀 Starting agent creation for session: {session_id}")
        print(f"📋 Requirements: {requirements}")

        if event_broadcaster and agent_integrator:
            # Register session
            event_broadcaster.connect_session(session_id, request.sid)
            join_room(session_id)

            # Start real agent creation process
            asyncio.create_task(
                agent_integrator.start_agent_creation(session_id, requirements)
            )

        else:
            # Fallback to mock workflow if integrator not available
            print("⚠️ Agent integrator not available, using mock workflow")
            if event_broadcaster:
                event_broadcaster.connect_session(session_id, request.sid)
                join_room(session_id)
                emit_mock_agent_creation_workflow(session_id)

        emit('agent_creation_started', {'session_id': session_id, 'status': 'initiated'})

    except Exception as e:
        print(f"❌ Error starting agent creation: {e}")
        emit('agent_creation_error', {'error': str(e)})

@socketio.on('join_session')
def handle_join_session(data):
    """Allow frontend to join a specific session room"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_session', {'session_id': session_id})
        print(f"🏠 Client {request.sid} joined session: {session_id}")

def emit_mock_agent_creation_workflow(session_id):
    """Mock agent creation workflow for testing (will be replaced with real integration)"""
    import threading
    import time

    def mock_workflow():
        try:
            time.sleep(1)
            event_broadcaster.emit_step(session_id, 'scenario', 'started', 'Analyzing your business requirements...')

            time.sleep(2)
            event_broadcaster.emit_step(session_id, 'scenario', 'completed', 'Business type determined: Restaurant')

            time.sleep(1)
            event_broadcaster.emit_step(session_id, 'prompts', 'started', 'Creating custom prompts for your agent...')

            time.sleep(3)
            event_broadcaster.emit_step(session_id, 'prompts', 'completed', 'Prompts created for restaurant agent')

            time.sleep(1)
            event_broadcaster.emit_step(
                session_id,
                'voice',
                'started',
                'Setting up voice profile for "Mario\'s Pizza Assistant"...',
                agent_name="Mario's Pizza Assistant"
            )

            time.sleep(2)
            event_broadcaster.emit_step(
                session_id,
                'voice',
                'completed',
                'Voice profile ready - alloy',
                agent_name="Mario's Pizza Assistant",
                voice_model="alloy"
            )

            time.sleep(1)
            event_broadcaster.emit_step(session_id, 'knowledge_base', 'started', 'Setting up knowledge base access...')

            time.sleep(2)
            event_broadcaster.emit_step(session_id, 'knowledge_base', 'completed', 'Knowledge base connected')

            time.sleep(1)
            event_broadcaster.emit_overall_status(session_id, 'completed', 'Agent creation successful! Your agent is ready to test.')

        except Exception as e:
            event_broadcaster.emit_overall_status(session_id, 'failed', 'Agent creation failed', error=str(e))

    # Run mock workflow in background thread
    thread = threading.Thread(target=mock_workflow)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    return render_template('product_search.html')

@app.route('/agent-test')
def agent_test():
    """Agent creation test page"""
    return render_template('agent_creation_test.html')

@app.route('/search_products', methods=['POST'])
def search_products():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({
                "success": False,
                "error": "Invalid request format. Expected JSON."
            }), 400

        user_query = data.get('query', '').strip()
        if not user_query:
            return jsonify({
                "success": False,
                "error": "Query parameter is required and cannot be empty"
            }), 400

        search_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": user_query,
            "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', '')
        }
        search_history.append(search_entry)

        print(f"🔍 Processing search: '{user_query}' from {request.remote_addr}")

        result = function_call(user_query)

        # ✅ Normalize result for frontend compatibility
        if result.get("success"):
            if result.get("exact_match") and "product" in result:
                result["results"] = {
                    "primary_matches": [result["product"]]
                }
                result["match_type"] = "exact"
            elif "products" in result:
                result["results"] = {
                    "primary_matches": result["products"]
                }
                result["match_type"] = "related"
            else:
                result["results"] = {
                    "primary_matches": []
                }
                result["match_type"] = "none"
        else:
            result["results"] = {
                "primary_matches": []
            }

        result['timestamp'] = search_entry['timestamp']
        result['processing_time'] = "< 1s"

        # Logging
        total_results = len(result["results"]["primary_matches"])
        if result.get('success'):
            print(f"✅ Search completed: {result['match_type']}, {total_results} results")
        else:
            print(f"❌ Search failed: {result.get('error', 'Unknown error')}")

        return jsonify(result), 200 if result.get('success') else 404

    except Exception as e:
        print(f"💥 Server error: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "query": user_query if 'user_query' in locals() else None
        }), 500

@app.route('/search_products', methods=['GET'])
def search_products_get():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter 'q' is required"
        }), 400
    return search_products_post_logic(query)

def search_products_post_logic(query):
    try:
        result = function_call(query)

        if result.get("success"):
            if result.get("exact_match") and "product" in result:
                result["results"] = {
                    "primary_matches": [result["product"]]
                }
                result["match_type"] = "exact"
            elif "products" in result:
                result["results"] = {
                    "primary_matches": result["products"]
                }
                result["match_type"] = "related"
            else:
                result["results"] = {
                    "primary_matches": []
                }
                result["match_type"] = "none"
        else:
            result["results"] = {
                "primary_matches": []
            }

        result['timestamp'] = datetime.now().isoformat()
        return jsonify(result), 200 if result.get('success') else 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "query": query
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Voice Agent Product Search",
        "timestamp": datetime.now().isoformat(),
        "total_searches": len(search_history)
    })

@app.route('/analytics', methods=['GET'])
def analytics():
    if not search_history:
        return jsonify({
            "total_searches": 0,
            "recent_searches": []
        })

    recent = search_history[-20:]
    total_searches = len(search_history)
    unique_queries = len(set(entry['query'].lower() for entry in search_history))

    return jsonify({
        "total_searches": total_searches,
        "unique_queries": unique_queries,
        "recent_searches": [
            {
                "query": entry['query'],
                "timestamp": entry['timestamp']
            } for entry in recent
        ]
    })

@app.route('/test', methods=['GET'])
def test_endpoint():
    sample_queries = [
        "iPhone 15 Pro",
        "gaming laptop under $1500",
        "wireless headphones under $200",
        "Samsung Galaxy S24"
    ]
    return render_template('test_page.html', sample_queries=sample_queries)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/search_products (POST/GET)",
            "/health (GET)",
            "/analytics (GET)",
            "/test (GET)",
            "/agent-event (POST)",
            "/action-event (POST)",
            "/ (GET - Frontend)"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

@app.route('/debug/search/<query>')
def debug_search(query):
    try:
        result = function_call(query)
        return f"""
        <h2>Debug Search: "{query}"</h2>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
{json.dumps(result, indent=2)}
        </pre>
        <br>
        <a href="/">← Back to Search</a>
        """
    except Exception as e:
        return f"<h2>Error:</h2><p>{str(e)}</p><a href='/'>← Back</a>"

# Production Bridge Webhook Endpoints
@app.route('/agent-event', methods=['POST'])
def handle_agent_event():
    """Receive agent creation events from LiveKit production bridge"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        event_data = request.get_json()
        session_id = event_data.get('session_id')

        if not session_id:
            return jsonify({"error": "session_id is required"}), 400

        # Forward to WebSocket clients
        if event_broadcaster:
            event_broadcaster.emit_step(
                session_id=session_id,
                step_name=event_data.get('step', 'unknown'),
                status=event_data.get('status', 'unknown'),
                message=event_data.get('message', ''),
                error=event_data.get('error'),
                **{k: v for k, v in event_data.items() if k not in ['session_id', 'step', 'status', 'message', 'error']}
            )

        print(f"📡 Received agent event: {event_data.get('step')}:{event_data.get('status')} - {event_data.get('message')}")
        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"❌ Error processing agent event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/action-event', methods=['POST'])
def handle_action_event():
    """Receive action-based events from LiveKit production bridge"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        event_data = request.get_json()
        session_id = event_data.get('session_id')
        action_type = event_data.get('action_type')

        if not session_id or not action_type:
            return jsonify({"error": "session_id and action_type are required"}), 400

        # Forward to WebSocket clients
        if event_broadcaster:
            event_broadcaster.emit_action(
                session_id=session_id,
                action_type=action_type,
                status=event_data.get('status', 'unknown'),
                message=event_data.get('message', ''),
                tool_data=event_data.get('tool_data'),
                error=event_data.get('error')
            )

        print(f"🎯 Received action event: {action_type}:{event_data.get('status')} - {event_data.get('message')}")
        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"❌ Error processing action event: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('ENV') != 'production'
    host = '0.0.0.0'

    print("🚀 Starting Voice Agent Product Search Webhook Server")
    print("=" * 60)
    print(f"🎯 Environment: {os.environ.get('ENV', 'development')}")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print("📡 API Endpoints:")
    print("  • POST /search_products - Main search endpoint")
    print("  • GET  /search_products?q=query - URL search")
    print("  • GET  /health - Health check")
    print("  • GET  /analytics - Search analytics")
    print("  • POST /agent-event - Production bridge events")
    print("  • POST /action-event - Production action events")
    print("  • GET  / - Frontend interface")
    print("  • GET  /test - Test page")
    print("  • GET  /agent-test - Agent creation test page")
    print("🌐 WebSocket Events:")
    print("  • start_agent_creation - Start agent creation")
    print("  • agent_creation_update - Real-time progress")
    print("=" * 60)

    try:
        test_result = function_call("test query")
        if test_result.get('success') is not None:
            print("✅ Voice agent function is working")
        else:
            print("⚠️ Voice agent function returned unexpected result")
    except Exception as e:
        print(f"❌ Voice agent function test failed: {e}")

    print(f"🌐 Server starting on {host}:{port}")
    print(f"🔗 WebSocket endpoint: ws://{host}:{port}/socket.io/")
    if not debug:
        print("🚀 Running in PRODUCTION mode")
    else:
        print("🔧 Running in DEVELOPMENT mode")
    print("=" * 60)

    # Check if running under Gunicorn
    if os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn'):
        # Running under Gunicorn - don't call socketio.run()
        print("🚀 Running under Gunicorn - SocketIO integrated")
    else:
        # Development mode - use SocketIO run
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
