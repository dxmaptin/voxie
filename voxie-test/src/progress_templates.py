"""
Safe Progress Message Templates for Agent Creation
Zero hallucination risk - all messages are predefined and factual
"""

from typing import Dict, Any, Optional

# Core progress steps for agent creation
PROGRESS_STEPS = [
    'scenario',
    'database_creation',
    'knowledge_base_setup',
    'voice',
    'prompts',
    'overall'
]

# Safe voice announcements - zero hallucination risk
VOICE_ANNOUNCEMENTS = {
    'scenario': {
        'started': "Analyzing your requirements...",
        'completed': "Requirements analyzed successfully",
        'failed': "Requirements analysis failed"
    },
    'database_creation': {
        'started': "Setting up database...",
        'completed': "Database is ready",
        'failed': "Database setup failed"
    },
    'knowledge_base_setup': {
        'started': "Connecting knowledge base...",
        'completed': "Knowledge base connected",
        'failed': "Knowledge base connection failed"
    },
    'voice': {
        'started': "Configuring voice profile...",
        'completed': "Voice profile ready",
        'failed': "Voice configuration failed"
    },
    'prompts': {
        'started': "Creating conversation prompts...",
        'completed': "Prompts configured",
        'failed': "Prompt creation failed"
    },
    'overall': {
        'started': "Finalizing agent setup...",
        'completed': "Your agent is ready to use!",
        'failed': "Agent creation encountered an issue"
    }
}

# Detailed progress messages for frontend display
DETAILED_MESSAGES = {
    'scenario': {
        'started': "Analyzing business requirements and use case...",
        'completed': "Business scenario identified and configured",
        'failed': "Unable to determine business requirements"
    },
    'database_creation': {
        'started': "Creating database schema and tables...",
        'completed': "Database successfully created with all required tables",
        'failed': "Database creation failed - check configuration"
    },
    'knowledge_base_setup': {
        'started': "Establishing connection to knowledge base system...",
        'completed': "Knowledge base integration active and ready",
        'failed': "Knowledge base connection failed - verify credentials"
    },
    'voice': {
        'started': "Setting up voice profile and speech parameters...",
        'completed': "Voice profile configured and tested successfully",
        'failed': "Voice configuration failed - check API settings"
    },
    'prompts': {
        'started': "Generating custom conversation prompts and responses...",
        'completed': "Conversation prompts configured for your use case",
        'failed': "Prompt generation failed - review requirements"
    },
    'overall': {
        'started': "Performing final configuration and testing...",
        'completed': "Agent creation successful! Ready for deployment.",
        'failed': "Agent creation failed - review logs for details"
    }
}

# Progress percentages for each step
PROGRESS_PERCENTAGES = {
    'scenario': {'started': 10, 'completed': 20},
    'database_creation': {'started': 20, 'completed': 40},
    'knowledge_base_setup': {'started': 40, 'completed': 60},
    'voice': {'started': 60, 'completed': 80},
    'prompts': {'started': 80, 'completed': 90},
    'overall': {'started': 90, 'completed': 100}
}

def get_voice_announcement(step: str, status: str) -> str:
    """
    Get safe voice announcement for agent progress
    Returns predefined message - zero hallucination risk
    """
    if step in VOICE_ANNOUNCEMENTS and status in VOICE_ANNOUNCEMENTS[step]:
        return VOICE_ANNOUNCEMENTS[step][status]
    return f"Agent creation {status}"

def get_detailed_message(step: str, status: str) -> str:
    """
    Get detailed progress message for frontend display
    Returns predefined message - zero hallucination risk
    """
    if step in DETAILED_MESSAGES and status in DETAILED_MESSAGES[step]:
        return DETAILED_MESSAGES[step][status]
    return f"Agent creation step {step} {status}"

def get_progress_percentage(step: str, status: str) -> int:
    """
    Get progress percentage for a specific step and status
    Returns factual completion percentage
    """
    if step in PROGRESS_PERCENTAGES and status in PROGRESS_PERCENTAGES[step]:
        return PROGRESS_PERCENTAGES[step][status]
    return 0

def should_announce_voice(step: str, status: str) -> bool:
    """
    Determine if this step should trigger voice announcement
    Reduces noise by only announcing important milestones
    """
    # Announce completed steps and critical failures
    if status == 'completed':
        return True
    if status == 'failed':
        return True
    # Only announce start of major steps
    if status == 'started' and step in ['database_creation', 'voice', 'overall']:
        return True
    return False

def get_step_emoji(step: str) -> str:
    """Get emoji representation for progress step"""
    emojis = {
        'scenario': '📋',
        'database_creation': '🗄️',
        'knowledge_base_setup': '🧠',
        'voice': '🎵',
        'prompts': '✍️',
        'overall': '🎯'
    }
    return emojis.get(step, '⚙️')

def format_progress_update(step: str, status: str, session_id: str,
                          include_percentage: bool = True) -> Dict[str, Any]:
    """
    Format a complete progress update with all safe information
    Returns structured data for consistent communication
    """
    return {
        'session_id': session_id,
        'step': step,
        'status': status,
        'voice_message': get_voice_announcement(step, status),
        'detailed_message': get_detailed_message(step, status),
        'progress_percentage': get_progress_percentage(step, status) if include_percentage else None,
        'should_announce': should_announce_voice(step, status),
        'emoji': get_step_emoji(step)
    }

# Validation functions
def is_valid_step(step: str) -> bool:
    """Check if step name is valid"""
    return step in PROGRESS_STEPS

def is_valid_status(status: str) -> bool:
    """Check if status is valid"""
    return status in ['started', 'completed', 'failed']