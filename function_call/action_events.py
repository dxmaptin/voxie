"""
Enhanced Event System with Specific Actions
Defines granular events for frontend UI components and specific tools
"""

from datetime import datetime
from typing import Optional, Dict, Any

class ActionBasedEventBroadcaster:
    """Event broadcaster with specific actionable events for frontend"""

    def __init__(self, base_broadcaster=None):
        self.base_broadcaster = base_broadcaster
        self.action_events = []

    def emit_action(self, session_id: str, action_type: str, status: str,
                   message: str, tool_data: Optional[Dict] = None, error: Optional[str] = None):
        """
        Emit specific action events for frontend UI

        Action Types:
        - database_creation, knowledge_base_setup, mcp_connection
        - connector_setup, scenario_generation, voice_configuration
        - prompt_optimization, testing_setup, deployment
        """

        event = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'action_type': action_type,
            'status': status,  # started, in_progress, completed, failed
            'message': message,
            'tool_data': tool_data or {},
            'error': error
        }

        self.action_events.append(event)

        # Also emit to base broadcaster for console logs
        if self.base_broadcaster:
            self.base_broadcaster.emit_step(
                session_id, action_type, status, message, error,
                **tool_data if tool_data else {}
            )

        print(f"🔧 ACTION: {action_type}:{status} - {message}")
        if tool_data:
            for key, value in tool_data.items():
                print(f"    {key}: {value}")

# Define specific action types for frontend
AGENT_CREATION_ACTIONS = {

    # 1. Database Creation Actions
    'database_creation': {
        'icon': '🗄️',
        'title': 'Database Setup',
        'description': 'Creating vector database for agent knowledge',
        'tool_component': 'DatabaseSetupTool',
        'steps': ['initializing', 'configuring', 'indexing', 'testing', 'completed']
    },

    # 2. Knowledge Base Actions
    'knowledge_base_setup': {
        'icon': '📚',
        'title': 'Knowledge Base',
        'description': 'Setting up knowledge base and document processing',
        'tool_component': 'KnowledgeBaseTool',
        'steps': ['uploading', 'processing', 'embedding', 'indexing', 'completed']
    },

    # 3. MCP (Model Context Protocol) Actions
    'mcp_connection': {
        'icon': '🔌',
        'title': 'MCP Integration',
        'description': 'Connecting Model Context Protocol services',
        'tool_component': 'MCPSetupTool',
        'steps': ['discovering', 'connecting', 'configuring', 'testing', 'completed']
    },

    # 4. Connector Actions
    'connector_setup': {
        'icon': '🌐',
        'title': 'External Connectors',
        'description': 'Setting up integrations (Slack, Teams, etc.)',
        'tool_component': 'ConnectorTool',
        'steps': ['authenticating', 'configuring', 'testing', 'completed']
    },

    # 5. Scenario Generation Actions
    'scenario_generation': {
        'icon': '🎭',
        'title': 'Scenario Creation',
        'description': 'Generating conversation scenarios and workflows',
        'tool_component': 'ScenarioTool',
        'steps': ['analyzing', 'generating', 'optimizing', 'validating', 'completed']
    },

    # 6. Voice Configuration Actions
    'voice_configuration': {
        'icon': '🎵',
        'title': 'Voice Setup',
        'description': 'Configuring voice model and speech parameters',
        'tool_component': 'VoiceConfigTool',
        'steps': ['selecting', 'testing', 'optimizing', 'completed']
    },

    # 7. Prompt Engineering Actions
    'prompt_optimization': {
        'icon': '✨',
        'title': 'Prompt Engineering',
        'description': 'Creating and optimizing AI prompts and instructions',
        'tool_component': 'PromptTool',
        'steps': ['generating', 'testing', 'optimizing', 'validating', 'completed']
    },

    # 8. Testing & Validation Actions
    'testing_setup': {
        'icon': '🧪',
        'title': 'Testing Suite',
        'description': 'Setting up automated testing and validation',
        'tool_component': 'TestingTool',
        'steps': ['configuring', 'running', 'validating', 'completed']
    },

    # 9. Deployment Actions
    'deployment': {
        'icon': '🚀',
        'title': 'Deployment',
        'description': 'Deploying agent to production environment',
        'tool_component': 'DeploymentTool',
        'steps': ['preparing', 'building', 'deploying', 'testing', 'completed']
    }
}

# Frontend Event Schema
FRONTEND_EVENT_SCHEMA = {
    'session_id': 'string',
    'action_type': 'string',  # One of AGENT_CREATION_ACTIONS keys
    'status': 'string',       # started, in_progress, completed, failed
    'message': 'string',      # Human readable message
    'progress': {
        'current_step': 'string',     # Current step within action
        'total_steps': 'number',      # Total steps for this action
        'percentage': 'number'        # 0-100 completion percentage
    },
    'tool_data': {
        'component': 'string',        # Frontend component to show
        'config': 'object',          # Configuration for the tool
        'results': 'object'          # Results/output from the tool
    },
    'error': 'string|null',
    'timestamp': 'string'
}

# Example Frontend Event
EXAMPLE_FRONTEND_EVENT = {
    'session_id': 'session_123',
    'action_type': 'database_creation',
    'status': 'in_progress',
    'message': 'Indexing documents in vector database...',
    'progress': {
        'current_step': 'indexing',
        'total_steps': 5,
        'percentage': 60
    },
    'tool_data': {
        'component': 'DatabaseSetupTool',
        'config': {
            'database_type': 'vector',
            'index_type': 'faiss',
            'dimensions': 1536
        },
        'results': {
            'documents_indexed': 150,
            'total_documents': 250,
            'index_size': '45MB'
        }
    },
    'error': None,
    'timestamp': '2025-09-28T15:30:25Z'
}