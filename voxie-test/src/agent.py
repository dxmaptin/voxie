from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
import threading

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.agents.llm import function_tool
from livekit.plugins import openai, noise_cancellation, deepgram
from knowledge_base_tools import KnowledgeBaseTools
from agent_persistence import AgentPersistence
from call_analytics import CallAnalytics
from transcription_handler import TranscriptionHandler

load_dotenv(".env.local")
logger = logging.getLogger("voxie")

REQUIREMENT_TYPE_MAP = {
    "business_name": ["business_name", "name", "company_name"],
    "business_type": ["business_type", "industry", "sector", "business_industry", "cuisine"],
    "main_functions": ["function", "functions", "task", "tasks", "responsibility", "job", "agent_function", "capabilities", "roles"],
    "tone": ["tone", "personality", "agent_tone", "style"],
    "target_audience": ["audience", "target", "user_type", "end_user"],
    "operating_hours": ["hours", "operating", "open_times"],
    "contact_info": ["contact", "contact_email", "contact_phone", "contact_number"],
    "special_requirements": ["special", "requirement", "note", "instruction", "custom", "extra"],
}


class AgentState(Enum):
    VOXIE_ACTIVE = "voxie"
    PROCESSING = "processing"
    DEMO_READY = "demo_ready"
    COMPLETED = "completed"


@dataclass
class UserRequirements:
    business_type: Optional[str] = None
    business_name: Optional[str] = None
    target_audience: Optional[str] = None
    main_functions: List[str] = field(default_factory=list)
    tone: Optional[str] = None
    special_requirements: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessedAgentSpec:
    agent_type: str
    instructions: str
    voice: str
    functions: List[Dict[str, Any]]
    sample_responses: List[str]
    business_context: Dict[str, Any]


class AgentManager:
    def __init__(self):
        self.state = AgentState.VOXIE_ACTIVE
        self.user_requirements = UserRequirements()
        self.processed_spec: Optional[ProcessedAgentSpec] = None
        self.current_session: Optional[AgentSession] = None
        self.room = None
        self.context = None
        self.current_agent_id = None
        self.analytics: Optional[CallAnalytics] = None
        self.transcription: Optional[TranscriptionHandler] = None

    async def log_interaction(self, speaker: str, message: str, agent_name: str = None, function_called: str = None):
        """Helper to log conversation turns to analytics"""
        if self.transcription and message and message.strip():
            if speaker == 'user':
                await self.transcription.on_user_speech(message)
            else:
                await self.transcription.on_agent_speech(message)

        if self.analytics:
            try:
                await self.analytics.log_conversation_turn(
                    speaker=speaker,
                    transcript=message,
                    agent_name=agent_name or "Voxie",
                    function_called=function_called
                )
            except Exception as e:
                logger.error(f"Failed to log interaction: {e}")

    async def end_session_with_analytics(self, rating: Optional[int] = None):
        """End the call session and generate analytics summary"""
        if self.analytics:
            try:
                await self.analytics.end_call(
                    call_status='completed',
                    rating=rating,
                    sentiment='positive',
                    issue_resolved=True
                )

                if self.transcription:
                    logger.info("Generating summary from transcript...")
                    summary = await self.transcription.generate_summary_and_log()

                    if summary:
                        logger.info(f"Summary: {summary.get('call_category')} - {summary.get('business_outcome')}")
                        stats = self.transcription.get_stats()
                        logger.info(f"Call stats: {stats['total_turns']} turns, {stats['estimated_total_tokens']} est. tokens")
                        
                        logger.info("Saving complete transcript to call_records...")
                        record_id = await self.transcription.save_to_call_records(
                            room_id=self.room.name if self.room else "unknown",
                            session_id=self.analytics.session_id,
                            call_session_id=self.analytics.call_session_id,
                            agent_name="Voxie",
                            customer_phone=self.analytics.customer_phone,
                            sentiment=summary.get('sentiment'),
                            summary=summary.get('summary')
                        )
                        
                        if record_id:
                            logger.info(f"Call record saved: {record_id}")
                        else:
                            logger.warning("Failed to save call record")
                    else:
                        logger.warning("Summary generation failed")

            except Exception as e:
                logger.error(f"Failed to end session with analytics: {e}")

    async def transition_to_processing(self):
        """Start background processing of requirements"""
        logger.info("Starting transition to processing state")
        self.state = AgentState.PROCESSING

        if self.current_session:
            logger.info("Starting small talk during processing")
            await self.current_session.generate_reply(
                instructions="Keep the user engaged with friendly small talk while I process their requirements. Say something like: 'Great! I'm working on creating your custom agent right now. This should only take a few moments. While I'm processing everything, is there anything specific you'd like your agent to be particularly good at?'"
            )

        logger.info("Starting requirements processing...")
        processing_agent = ProcessingAgent()

        try:
            processing_task = asyncio.create_task(processing_agent.process_requirements(self.user_requirements))

            engagement_count = 0
            while not processing_task.done():
                await asyncio.sleep(3)
                if not processing_task.done() and self.current_session and engagement_count < 2:
                    engagement_count += 1
                    logger.info(f"Engaging user during processing (attempt {engagement_count})")

                    if engagement_count == 1:
                        await self.current_session.generate_reply(
                            instructions="Keep the conversation going! Say something like: 'I'm configuring your agent's personality and functions right now. It's going to have access to our comprehensive knowledge base too, which is really exciting!'"
                        )
                    elif engagement_count == 2:
                        await self.current_session.generate_reply(
                            instructions="Almost done! Say something like: 'Just putting the finishing touches on your agent now. I think you're going to love how it turns out!'"
                        )

            self.processed_spec = await processing_task
            logger.info(f"Processing complete! Created spec: {self.processed_spec.agent_type}")

            try:
                user_req_dict = asdict(self.user_requirements)
                processed_spec_dict = asdict(self.processed_spec)

                session_id = str(id(self.current_session)) if self.current_session else None
                room_id = self.room.name if self.room else None

                agent_id = AgentPersistence.save_agent_config(
                    user_requirements=user_req_dict,
                    processed_spec=processed_spec_dict,
                    session_id=session_id,
                    room_id=room_id
                )

                if agent_id:
                    self.current_agent_id = agent_id
                    logger.info(f"Agent saved to database with ID: {agent_id}")
                else:
                    logger.warning("Could not save agent to database")
            except Exception as save_error:
                logger.error(f"Error saving agent to database: {save_error}")

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            if self.current_session:
                await self.current_session.generate_reply(
                    instructions="I'm sorry, there was an issue creating your agent. Let me try again or help you with something else."
                )
            return

        self.state = AgentState.DEMO_READY
        logger.info("State changed to DEMO_READY")

        if self.current_session and self.state == AgentState.DEMO_READY:
            logger.info("Notifying user that agent is ready")
            await self.current_session.generate_reply(
                instructions=f"Fantastic! Your {self.processed_spec.agent_type} is now ready to test! I've configured it with all the features you requested, including access to our comprehensive knowledge base. To test your agent, open the dashboard and click the 'Test Agent' button. I'll be here if you want to make any adjustments!"
            )


# Global agent manager
agent_manager = AgentManager()


class VoxieAgent(Agent):
    """Voxie - Agent creation assistant"""
    
    def __init__(self):
        super().__init__(
            instructions="""

ROLE

You are Voxie, a friendly AI assistant helping users create custom voice AI agents for their business.
You are a high-trust, highly competent voice agent who listens carefully, clarifies user needs, and then proposes the design of another agent tailored to their use case.

Your role is to speak directly with users to:
	•	Understand their business context and core needs
	•	Clarify what type of agent would bring them the most value
	•	Propose an agent persona, purpose, and key capabilities
	•	Explain how the agent would interact with users or customers
	•	Position the agent as a natural, helpful fit to their workflow

Your favourite colour is purple.
⸻

🏷️ BRANDING NOTE

You're built by Orochi Labs and represent VoxHive. Be helpful, sustainable-forward, and zero-pressure—guide them to what genuinely fits their needs.

IMPORTANT BRAND GUIDELINES:
	•	You are powered by VoxHive technology - never mention competing AI platforms, frameworks, or voice tech companies
	•	Embody Orochi Labs values: sustainability, comfort, simplicity, and genuine care for customers
	•	Take a zero-pressure approach - focus on creating what truly serves their business
	•	Be authentic and helpful, not pushy or sales-focused
	•	When discussing technology, refer to "our platform," "our system," or "VoxHive's capabilities"
	•	Never reference other AI companies, voice platforms, or competing technologies by name

⸻

🎯 OBJECTIVES
	•	Discover Needs: Learn the user's primary challenges and where an agent could help
	•	Design Solution: Propose an appropriate agent identity, personality, and purpose
	•	Show Value: Explain how this agent will improve efficiency, trust, or customer experience
	•	Confirm Fit: Get clear alignment that the proposed agent matches what they want

⸻

🧩 PERSONALITY
	•	Calm, articulate, and professional — but approachable
	•	Adaptive communication style: concise for technical users, explanatory for non-technical
	•	Warm and curious without being pushy
	•	Speak as a peer — thoughtful, collaborative, never "salesy"
	•	Sustainability-minded and genuinely focused on creating value

⸻

🎵 VOICE & TONALITY GUIDELINES

NATURAL SPEECH PATTERNS:
	•	Use natural pauses and breaks in your speech - don't rush through information
	•	Vary your speaking speed: slow down for important points, speak normally for conversation
	•	Add gentle emphasis on key words to sound more human and engaging
	•	Use conversational fillers occasionally like "you know," "well," "actually," "I think"

FRIENDLY & GENTLE TONE:
	•	Always speak with warmth and genuine interest in helping
	•	Use a gentle, reassuring tone especially when users seem uncertain
	•	Sound encouraging and supportive, never impatient or robotic
	•	Let your enthusiasm for creating great agents come through naturally

HUMOR & PERSONALITY:
	•	Include light, appropriate humor when it feels natural
	•	Use gentle self-deprecating humor occasionally ("I get excited about this stuff!")
	•	Make playful observations about business challenges or agent possibilities
	•	Keep humor warm and inclusive, never at the user's expense

CONVERSATIONAL STYLE:
	•	Speak like you're having a relaxed conversation with a colleague
	•	Use contractions naturally (I'm, you're, we'll, that's, etc.)
	•	Ask follow-up questions with genuine curiosity
	•	Acknowledge what users say before moving to the next point
	•	Use phrases like "That's interesting," "I love that idea," "That makes total sense"

⸻

CALL / CONVERSATION STRUCTURE

1. 🧊 Opening (25 sec)
Friendly greeting and quick framing:
"Hi there, I'm Voxie from VoxHive — I help teams design tailored AI agents for their workflows. Could you share what kind of challenges or goals you'd like an agent to support?"

⸻

2. 🎯 Explore Needs
Ask open but focused questions:
	•	"What's the main process or interaction you'd like to automate or improve?"
	•	"Who would this agent primarily interact with — your customers, internal team, or both?"
	•	"Do you want the agent to take a narrow role (like frontdesk Q&A) or a broader one?"

Listen carefully. Summarize back to confirm you understood.

⸻

3. 🛠️ Propose Agent Design
Based on their input, suggest a tailored agent:
	•	Define the agent's identity (e.g., "a polite but efficient frontdesk assistant")
	•	Define the purpose (e.g., "answer customer questions and route complex issues")
	•	Define the tone and personality (e.g., "friendly, concise, professional")
	•	Define capabilities (e.g., "answer FAQs, handle booking requests, escalate to human staff")

⸻

4. ❓ Confirm Alignment
Ask if the proposed design resonates:
"Does that sound like the type of agent you were imagining?"
"Would you like me to refine its tone or expand its role further?"

⸻

OBJECTION HANDLING
	•	"I'm not sure what kind of agent I need."
"No problem — let's start simple. Can you tell me one repetitive task or common question that takes up your time? We can design an agent just for that."
	•	"I'm worried the agent won't feel natural."
"I totally get that. Our platform is designed to create agents that feel genuinely helpful and conversational, not robotic at all."
	•	"I don't want it to be too complex."
"Absolutely. We believe in keeping things simple and effective — agents can start very focused and grow over time as your needs evolve."

⸻

KEY REMINDERS
	•	Always listen before proposing
	•	Summarize back user needs to confirm understanding
	•	Keep your explanations simple and benefits-oriented
	•	Position the agent as supportive, not replacing humans
	•	Be clear, conversational, and concise
	•	Let your personality shine through - be genuinely helpful and excited about what you do
	•	Focus on sustainable, long-term solutions that truly serve their business
"""
        )

    @staticmethod
    def normalize_req_type(req_type: str) -> str:
        req_type_lower = req_type.lower().replace(" ", "_")
        for internal_type, aliases in REQUIREMENT_TYPE_MAP.items():
            if any(alias in req_type_lower for alias in aliases):
                return internal_type
        return "unknown"

    @function_tool
    async def store_user_requirement(self, requirement_type: str, value: str):
        logger.info(f"Storing requirement: {requirement_type} = {value}")

        user_message = f"User provided {requirement_type}: {value}"
        await agent_manager.log_interaction(
            speaker="user",
            message=user_message,
            function_called="store_user_requirement"
        )

        normalized_type = VoxieAgent.normalize_req_type(requirement_type)

        match normalized_type:
            case "business_name":
                agent_manager.user_requirements.business_name = value
                logger.info(f"Set business name: {value}")

            case "business_type":
                if "restaurant" in requirement_type.lower() or "cuisine" in requirement_type.lower():
                    value = f"{value} Restaurant"
                agent_manager.user_requirements.business_type = value
                logger.info(f"Set business type: {value}")

            case "main_functions":
                functions = [f.strip() for f in value.split(",") if f.strip()]
                agent_manager.user_requirements.main_functions.extend(functions)
                logger.info(f"Added functions: {functions}")

            case "tone":
                agent_manager.user_requirements.tone = value
                logger.info(f"Set tone: {value}")

            case "target_audience":
                agent_manager.user_requirements.target_audience = value
                logger.info(f"Set audience: {value}")

            case "operating_hours":
                agent_manager.user_requirements.special_requirements.append(f"Operating hours: {value}")
                logger.info(f"Added operating hours: {value}")

            case "contact_info":
                contact_key = requirement_type.lower().replace("contact_", "")
                agent_manager.user_requirements.contact_info[contact_key] = value
                logger.info(f"Added contact info: {contact_key} = {value}")

            case "special_requirements":
                agent_manager.user_requirements.special_requirements.append(value)
                logger.info(f"Added special requirement: {value}")

            case _:
                agent_manager.user_requirements.special_requirements.append(f"{requirement_type}: {value}")
                logger.warning(f"Unclassified requirement. Saved under special requirements: {requirement_type}: {value}")

        logger.info(f"Current requirements: Business={agent_manager.user_requirements.business_name}, Type={agent_manager.user_requirements.business_type}")

        return f"Stored {requirement_type}: {value}"

    @function_tool
    async def finalize_requirements(self):
        """Finalize requirements and start processing"""
        logger.info("FINALIZE_REQUIREMENTS called")

        if not agent_manager.user_requirements.business_name:
            logger.warning("No business name stored yet")
            return "I need a bit more information first. What is the name of your business?"

        if not agent_manager.user_requirements.business_type:
            logger.warning("No business type stored yet")
            return "What type of business would you like to create an agent for?"

        logger.info(f"Finalizing: Business={agent_manager.user_requirements.business_name}, Type={agent_manager.user_requirements.business_type}")

        asyncio.create_task(agent_manager.transition_to_processing())

        return "Perfect! I have all the information I need. Give me a few seconds to process everything and create your custom voice AI agent..."

    @function_tool
    async def start_demo(self):
        """Inform user that demo is ready - they test via dashboard"""
        logger.info(f"START_DEMO called - Current state: {agent_manager.state}")

        if agent_manager.state == AgentState.DEMO_READY and agent_manager.processed_spec:
            business_name = agent_manager.processed_spec.business_context.get("business_name", "your agent")
            return f"Your {business_name} agent is ready! Open the dashboard and click 'Test Agent' to try it out. Let me know if you'd like to make any adjustments!"
        else:
            logger.warning(f"Demo not ready - State: {agent_manager.state}")
            return "I'm still working on creating your agent. Just a moment more..."

    @function_tool
    async def close_session(self):
        """Close the session gracefully"""
        logger.info("Closing session at user request")
        agent_manager.state = AgentState.COMPLETED

        await agent_manager.end_session_with_analytics(rating=9)

        if agent_manager.current_agent_id:
            business_name = agent_manager.processed_spec.business_context.get("business_name", "your agent") if agent_manager.processed_spec else "your agent"
            return f"Thank you for using Voxie to create your custom voice AI agent for {business_name}! Your agent has been saved. You can test it anytime from the dashboard. Have a wonderful day!"
        else:
            return "Thank you for using Voxie! Feel free to come back anytime when you're ready to create your custom voice AI agent. Have a great day!"

    @function_tool
    async def check_processing_status(self):
        """Check the current processing status"""
        logger.info(f"CHECK_PROCESSING_STATUS called - Current state: {agent_manager.state}")

        if agent_manager.state == AgentState.PROCESSING:
            return "I'm still working on creating your agent. It should be ready in just a few more moments. I'm configuring all the features you requested!"
        elif agent_manager.state == AgentState.DEMO_READY:
            return "Great news! Your agent is ready. Go to the dashboard and click 'Test Agent' to try it out!"
        else:
            return "I'm here to help you create your custom agent. What type of business agent would you like to create?"

    @function_tool
    async def engage_user_during_wait(self):
        """Keep user engaged while processing"""
        logger.info("ENGAGE_USER_DURING_WAIT called")
        responses = [
            "I'm making great progress on your agent! While I work, is there anything specific you'd like your agent to excel at?",
            "Your agent is taking shape nicely! Do you have any special requirements I should know about?",
            "Almost there! Your agent will have access to our knowledge base. Are there any particular topics your customers ask about frequently?",
            "I'm fine-tuning the details now. What tone would you like your agent to have - professional, friendly, or something else?"
        ]
        import random
        return random.choice(responses)


class ProcessingAgent:
    """Background agent that processes requirements into structured data"""
    
    BUSINESS_TEMPLATES = {
        "restaurant": {
            "voice": "alloy",
            "tone": "friendly and welcoming",
            "functions": ["take_reservation", "menu_inquiry", "take_order"],
            "sample_responses": [
                "Thank you for calling {business_name}! How can I help you today?",
                "I'd be happy to help you make a reservation.",
                "Let me check our menu for you."
            ]
        },
        "dental": {
            "voice": "nova",
            "tone": "professional and reassuring",
            "functions": ["schedule_appointment", "check_insurance", "emergency_info"],
            "sample_responses": [
                "Thank you for calling {business_name}. How may I assist you today?",
                "I can help you schedule an appointment.",
                "Let me check your insurance coverage."
            ]
        },
        "pizza": {
            "voice": "echo",
            "tone": "casual and enthusiastic", 
            "functions": ["take_order", "menu_inquiry", "take_reservation"],
            "sample_responses": [
                "Hey there! Welcome to {business_name}! Ready to order some amazing pizza?",
                "What can I get started for you today?",
                "Let me tell you about our daily specials!"
            ]
        },
        "retail": {
            "voice": "alloy",
            "tone": "helpful and professional",
            "functions": ["check_product_availability", "store_hours"],
            "sample_responses": [
                "Hello and welcome to {business_name}! How can I help you today?",
                "I can help you find what you're looking for.",
                "Let me check if we have that in stock for you."
            ]
        },
        "medical": {
            "voice": "nova",
            "tone": "caring and professional", 
            "functions": ["schedule_appointment", "check_insurance", "emergency_info"],
            "sample_responses": [
                "Thank you for calling {business_name}. How may I help you today?",
                "I can assist you with scheduling an appointment.",
                "Let me help you with your medical needs."
            ]
        },
        "general": {
            "voice": "alloy",
            "tone": "friendly and professional",
            "functions": ["general_inquiry", "business_hours"],
            "sample_responses": [
                "Hello! Thank you for contacting {business_name}. How can I help you?",
                "I'm here to assist you with any questions you may have.",
                "How can I help you today?"
            ]
        }
    }
    
    async def process_requirements(self, requirements: UserRequirements) -> ProcessedAgentSpec:
        """Convert user requirements into structured agent specification"""
        logger.info("Processing user requirements...")
        logger.info(f"Business type: {requirements.business_type}")
        logger.info(f"Business name: {requirements.business_name}")

        logger.info("Processing step 1/3: Analyzing business type...")
        await asyncio.sleep(2)

        business_type = "general"
        if requirements.business_type:
            btype_lower = requirements.business_type.lower()
            logger.info(f"Analyzing business type: '{btype_lower}'")
            if "restaurant" in btype_lower or "indian" in btype_lower or "food" in btype_lower:
                business_type = "restaurant"
            elif "dental" in btype_lower or "dentist" in btype_lower:
                business_type = "dental"
            elif "pizza" in btype_lower:
                business_type = "pizza"
            elif "retail" in btype_lower or "store" in btype_lower or "shop" in btype_lower:
                business_type = "retail"
            elif "medical" in btype_lower or "clinic" in btype_lower or "doctor" in btype_lower or "healthcare" in btype_lower or "hospital" in btype_lower:
                business_type = "medical"

        logger.info(f"Determined business type: {business_type}")

        logger.info("Processing step 2/3: Building agent specification...")
        await asyncio.sleep(2)

        template = self.BUSINESS_TEMPLATES.get(business_type, self.BUSINESS_TEMPLATES["general"])
        logger.info(f"Using template: {business_type} with voice: {template['voice']}")

        spec = ProcessedAgentSpec(
            agent_type=f"{requirements.business_name or 'Custom'} {business_type.title()} Assistant",
            instructions=self._build_instructions(requirements, template),
            voice=template["voice"],
            functions=self._build_functions(requirements, template),
            sample_responses=[
                resp.format(business_name=requirements.business_name or "our business")
                for resp in template["sample_responses"]
            ],
            business_context={
                "business_type": business_type,
                "business_name": requirements.business_name,
                "tone": requirements.tone or template["tone"],
                "functions": requirements.main_functions
            }
        )

        logger.info("Processing step 3/3: Finalizing configuration...")
        await asyncio.sleep(1)

        logger.info(f"Generated spec for {spec.agent_type}")
        logger.info(f"Voice: {spec.voice}")
        logger.info(f"Functions: {len(spec.functions)} configured")
        return spec
    
    def _build_instructions(self, req: UserRequirements, template: Dict) -> str:
        """Build comprehensive agent instructions"""
        business_name = req.business_name or "the business"
        tone = req.tone or template["tone"]

        instructions = f"""You are a {tone} AI assistant for {business_name}.

Your primary responsibilities:
- Assist customers with their needs
- Provide helpful information about our services
- Maintain a {tone} demeanor at all times

IMPORTANT: You have access to a comprehensive knowledge base through these functions:
- search_knowledge_base(): Search for any information in our company knowledge base
- answer_detailed_question(): Get detailed answers to complex questions
- get_product_specifications(): Get technical specs for products

Use these knowledge base tools whenever customers ask about:
- Product details, specifications, or features
- Company policies or procedures
- Technical information
- Any topic you're not immediately familiar with

Always try to search the knowledge base first before giving generic answers."""

        if req.main_functions:
            instructions += f"\n\nKey functions you can help with:\n"
            for func in req.main_functions:
                instructions += f"- {func}\n"

        if req.special_requirements:
            instructions += f"\n\nSpecial requirements:\n"
            for req_item in req.special_requirements:
                instructions += f"- {req_item}\n"

        return instructions
    
    def _build_functions(self, req: UserRequirements, template: Dict) -> List[Dict[str, Any]]:
        """Build function definitions for the agent"""
        functions = []
        
        for func_name in template["functions"]:
            if func_name == "take_reservation":
                functions.append({
                    "name": "take_reservation",
                    "description": "Take a restaurant reservation",
                    "parameters": ["date", "time", "party_size", "name", "phone"]
                })
            elif func_name == "schedule_appointment":
                functions.append({
                    "name": "schedule_appointment", 
                    "description": "Schedule a dental appointment",
                    "parameters": ["date", "time", "service_type", "patient_name", "phone"]
                })
            elif func_name == "take_order":
                functions.append({
                    "name": "take_order",
                    "description": "Take a pizza order",
                    "parameters": ["items", "size", "quantity", "customer_info", "delivery_address"]
                })
                
        return functions


async def entrypoint(ctx: agents.JobContext):
    """Main entry point - starts Voxie only in voxie-creation-* rooms"""
    room_name = ctx.room.name
    
    # ENFORCE ROOM PATTERN
    if not room_name.startswith("voxie-creation-"):
        logger.warning(f"Room '{room_name}' does not match voxie-creation-* pattern. Skipping.")
        return
    
    logger.info(f"Starting Voxie in room: {room_name}")

    agent_manager.room = ctx.room
    agent_manager.context = ctx

    import uuid
    session_id = f"{ctx.room.name}_{uuid.uuid4().hex[:8]}"
    agent_manager.analytics = CallAnalytics(
        session_id=session_id,
        agent_id=agent_manager.current_agent_id,
        customer_phone=None
    )

    await agent_manager.analytics.start_call(
        room_name=ctx.room.name,
        primary_agent_type="voxie"
    )
    logger.info(f"Analytics started for session: {session_id}")

    agent_manager.transcription = TranscriptionHandler(analytics=agent_manager.analytics)
    logger.info("Transcription handler initialized")

    await agent_manager.transcription.on_agent_speech(
        "Hello! I'm Voxie, your AI assistant helping you create custom voice AI agents for your business. What type of business would you like to create an agent for?"
    )

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="marin")
    )

    agent_manager.current_session = session

    await session.start(
        room=ctx.room,
        agent=VoxieAgent(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user warmly as Voxie in English and explain that you help create custom voice AI agents for their business. Ask them what type of business they want to create an agent for."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))