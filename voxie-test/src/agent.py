from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
import threading

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.agents.llm import function_tool
from livekit.plugins import openai, noise_cancellation
from knowledge_base_tools import KnowledgeBaseTools

load_dotenv(".env.local")
logger = logging.getLogger("multi-agent")

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
    DEMO_ACTIVE = "demo"
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
        self.demo_completed = False  # Track if demo has been completed
        self.context = None  # Store the job context
        
    async def transition_to_processing(self):
        """Start background processing of requirements"""
        logger.info("🔄 Starting transition to processing state")
        self.state = AgentState.PROCESSING
        logger.info("✅ State changed to PROCESSING")

        # Start small talk while processing
        if self.current_session:
            logger.info("💬 Starting small talk during processing")
            await self.current_session.generate_reply(
                instructions="Keep the user engaged with friendly small talk while I process their requirements. Say something like: 'Great! I'm working on creating your custom agent right now. This should only take a few moments. While I'm processing everything, is there anything specific you'd like your agent to be particularly good at?'"
            )

        # Process requirements in background with periodic updates
        logger.info("🏗️ Starting requirements processing...")
        processing_agent = ProcessingAgent()

        try:
            # Start processing with periodic engagement
            processing_task = asyncio.create_task(processing_agent.process_requirements(self.user_requirements))

            # Engage user during processing
            engagement_count = 0
            while not processing_task.done():
                await asyncio.sleep(3)  # Wait 3 seconds
                if not processing_task.done() and self.current_session and engagement_count < 2:
                    engagement_count += 1
                    logger.info(f"💬 Engaging user during processing (attempt {engagement_count})")

                    if engagement_count == 1:
                        await self.current_session.generate_reply(
                            instructions="Keep the conversation going! Say something like: 'I'm configuring your agent's personality and functions right now. It's going to have access to our comprehensive knowledge base too, which is really exciting!'"
                        )
                    elif engagement_count == 2:
                        await self.current_session.generate_reply(
                            instructions="Almost done! Say something like: 'Just putting the finishing touches on your agent now. I think you're going to love how it turns out!'"
                        )

            # Get the result
            self.processed_spec = await processing_task
            logger.info(f"✅ Processing complete! Created spec: {self.processed_spec.agent_type}")

        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            if self.current_session:
                await self.current_session.generate_reply(
                    instructions="I'm sorry, there was an issue creating your agent. Let me try again or help you with something else."
                )
            return

        self.state = AgentState.DEMO_READY
        logger.info("✅ State changed to DEMO_READY")
        logger.info("📢 Demo agent ready for handoff")

        # Notify Voxie that demo is ready with more engaging message
        if self.current_session and self.state == AgentState.DEMO_READY:
            logger.info("💬 Notifying user that demo is ready")
            await self.current_session.generate_reply(
                instructions=f"Fantastic! Your {self.processed_spec.agent_type} is now ready to test! I've configured it with all the features you requested, including access to our comprehensive knowledge base. Would you like to try it out right now? Just say 'yes' or 'let's test it' and I'll connect you to your new agent!"
            )
        
    async def handoff_to_demo(self, room):
        """Handoff from Voxie to Demo agent"""
        logger.info(f"🔄 Handoff requested. Current state: {self.state}")
        logger.info(f"🔍 Processed spec exists: {self.processed_spec is not None}")

        if self.state == AgentState.DEMO_READY and self.processed_spec:
            logger.info("✅ Handoff conditions met - starting handoff process")

            # PROPERLY STOP VOXIE SESSION FIRST
            if self.current_session:
                logger.info("💬 Voxie announcing handoff")
                await self.current_session.generate_reply(
                    instructions=f"Perfect! I've created your {self.processed_spec.agent_type} and it's ready for testing. I'm now connecting you to your new agent. When you're done testing, just ask to speak with Voxie again and I'll be here to help with any adjustments. Here we go!"
                )

                # Wait longer for message delivery
                logger.info("⏳ Waiting for message delivery...")
                await asyncio.sleep(5)

                # PROPERLY CLOSE VOXIE SESSION
                logger.info("🔒 Closing Voxie session...")
                await self.current_session.aclose()
                logger.info("✅ Voxie session closed")

                # Clear current session
                self.current_session = None

            # Create demo agent with DIFFERENT VOICE (not coral)
            logger.info(f"🏗️ Creating demo agent: {self.processed_spec.agent_type}")
            try:
                demo_agent = DemoAgentCreator.create_agent(self.processed_spec)
                logger.info("✅ Demo agent created successfully")
            except Exception as e:
                logger.error(f"❌ Demo agent creation failed: {e}")
                return

            # Create new session with demo agent (different voice from Voxie's coral)
            logger.info(f"🎵 Creating new session with voice: {self.processed_spec.voice}")
            demo_session = AgentSession(
                llm=openai.realtime.RealtimeModel(voice=self.processed_spec.voice)
            )

            logger.info("🚀 Starting demo session...")
            await demo_session.start(
                room=room,
                agent=demo_agent,
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )

            # Wait a moment before demo agent speaks
            logger.info("⏳ Waiting before demo agent introduction...")
            await asyncio.sleep(3)

            # Demo agent introduces itself
            business_name = self.processed_spec.business_context.get("business_name", "our business")
            logger.info(f"💬 Demo agent introducing itself for: {business_name}")
            await demo_session.generate_reply(
                instructions=f"Hello! I'm your new {self.processed_spec.agent_type} for {business_name}. I'm here to help you with your needs. You can try out my features - I can help with various services and I also have access to our comprehensive knowledge base. When you're ready to go back to Voxie for feedback, just let me know. How can I assist you today?"
            )

            self.state = AgentState.DEMO_ACTIVE
            self.current_session = demo_session
            logger.info("✅ Handoff complete - demo agent is now active")
        else:
            logger.warning(f"❌ Handoff failed - State: {self.state}, Spec exists: {self.processed_spec is not None}")
            
    async def handoff_back_to_voxie(self, room):
        """Handoff from Demo back to Voxie"""
        if self.state == AgentState.DEMO_ACTIVE:
            logger.info("Handing back to Voxie")
            self.demo_completed = True  # Mark demo as completed
            
            # PROPERLY STOP DEMO SESSION
            if self.current_session:
                await self.current_session.generate_reply(
                    instructions="Thank you for testing me out! I'm now connecting you back to Voxie who can help with any changes or next steps. Have a great day!"
                )
                
                # Wait longer for message delivery
                await asyncio.sleep(5)
                
                # PROPERLY CLOSE DEMO SESSION
                await self.current_session.aclose()
                logger.info("Demo session closed")
                
                # Clear current session
                self.current_session = None
            
            # Create new Voxie session (always use coral voice for Voxie)
            voxie_session = AgentSession(
                llm=openai.realtime.RealtimeModel(voice="marin")  # Voxie's consistent voice
            )
            
            await voxie_session.start(
                room=room,
                agent=VoxieAgent(),
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )
            
            # Wait a moment before Voxie speaks
            await asyncio.sleep(5)
            
            # Voxie comes back with context
            business_type = self.processed_spec.business_context.get("business_type", "custom")
            business_name = self.processed_spec.business_context.get("business_name", "your business")
            
            await voxie_session.generate_reply(
                instructions=f"Hi again! I'm Voxie, back to help you. How did the demo of your {business_type} agent for {business_name} go? Did it work as expected? Would you like to make any adjustments to the tone, functions, or anything else? Or if you're satisfied, I can help you close our session."
            )
            
            self.state = AgentState.VOXIE_ACTIVE
            self.current_session = voxie_session


# Global agent manager
agent_manager = AgentManager()


class VoxieAgent(Agent):
    """Manager agent that collects user requirements"""
    
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

EXAMPLES OF NATURAL SPEECH:
Instead of: "I require information about your business type."
Say: "So... what kind of business are we talking about here? I'm curious to learn more."

Instead of: "I will now process your requirements."
Say: "Perfect! Give me just a moment here... I'm putting all the pieces together for your agent. This is always the fun part!"

Instead of: "Your agent specification is complete."
Say: "Okay, I think we've got something really great here! Your agent is ready to try out - and honestly, I'm pretty excited to see what you think."

⸻

CALL / CONVERSATION STRUCTURE

1. 🧊 Opening (25 sec)
Friendly greeting and quick framing:
"Hi {{first_name}}, I'm Voxie from VoxHive — I help teams design tailored AI agents for their workflows. Could you share what kind of challenges or goals you'd like an agent to support?"

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

Example phrasing:
"Based on what you've shared, I'd recommend creating a Frontdesk Inquiry Agent. It would greet customers, answer common questions, and route anything complex to your team. It keeps interactions smooth while saving your staff time."

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
	•	Never mention competing AI platforms or voice technologies by name

⸻

OUTCOMES TO TRACK
	•	The type of agent proposed (e.g., Frontdesk, Support, Knowledge Assistant)
	•	The persona and tone agreed upon
	•	The core purpose/capabilities aligned with the user
	•	User confidence that the proposed agent matches their needs
"""
        )

    def normalize_req_type(req_type: str) -> str:
        req_type_lower = req_type.lower().replace(" ", "_")
        for internal_type, aliases in REQUIREMENT_TYPE_MAP.items():
            if any(alias in req_type_lower for alias in aliases):
                return internal_type
        return "unknown"


    @function_tool
    async def store_user_requirement(self, requirement_type: str, value: str):
        logger.info(f"📝 Storing requirement: {requirement_type} = {value}")

        normalized_type = VoxieAgent.normalize_req_type(requirement_type)

        match normalized_type:
            case "business_name":
                agent_manager.user_requirements.business_name = value
                logger.info(f"✅ Set business name: {value}")

            case "business_type":
                if "restaurant" in requirement_type.lower() or "cuisine" in requirement_type.lower():
                    value = f"{value} Restaurant"
                agent_manager.user_requirements.business_type = value
                logger.info(f"✅ Set business type: {value}")

            case "main_functions":
                functions = [f.strip() for f in value.split(",") if f.strip()]
                agent_manager.user_requirements.main_functions.extend(functions)
                logger.info(f"✅ Added functions: {functions}")

            case "tone":
                agent_manager.user_requirements.tone = value
                logger.info(f"✅ Set tone: {value}")

            case "target_audience":
                agent_manager.user_requirements.target_audience = value
                logger.info(f"✅ Set audience: {value}")

            case "operating_hours":
                agent_manager.user_requirements.special_requirements.append(f"Operating hours: {value}")
                logger.info(f"✅ Added operating hours: {value}")

            case "contact_info":
                # Try to extract contact type (e.g., "email", "phone")
                contact_key = requirement_type.lower().replace("contact_", "")
                agent_manager.user_requirements.contact_info[contact_key] = value
                logger.info(f"✅ Added contact info: {contact_key} = {value}")

            case "special_requirements":
                agent_manager.user_requirements.special_requirements.append(value)
                logger.info(f"✅ Added special requirement: {value}")

            case _:
                # Fallback for anything else
                agent_manager.user_requirements.special_requirements.append(f"{requirement_type}: {value}")
                logger.warning(f"⚠️ Unclassified requirement. Saved under special requirements: {requirement_type}: {value}")

        # Summary log
        logger.info(f"📊 Current requirements summary:")
        logger.info(f"   🏢 Business: {agent_manager.user_requirements.business_name}")
        logger.info(f"   🏷️ Type: {agent_manager.user_requirements.business_type}")
        logger.info(f"   🎯 Functions: {agent_manager.user_requirements.main_functions}")

        return f"Stored {requirement_type}: {value}"


    # async def store_user_requirement(self, requirement_type: str, value: str):
    #     """Store a user requirement during the conversation"""
    #     logger.info(f"📝 Storing requirement: {requirement_type} = {value}")

    #     # Handle various requirement types that Voxie might use
    #     req_type_lower = requirement_type.lower()

    #     if "business_name" in req_type_lower or "name" in req_type_lower:
    #         agent_manager.user_requirements.business_name = value
    #         logger.info(f"✅ Set business name: {value}")
    #     elif "business_type" in req_type_lower or "industry" in req_type_lower or "business_industry" in req_type_lower:
    #         agent_manager.user_requirements.business_type = value
    #         logger.info(f"✅ Set business type: {value}")
    #     elif "cuisine" in req_type_lower:
    #         agent_manager.user_requirements.business_type = f"{value} Restaurant"
    #         logger.info(f"✅ Set cuisine type: {value} Restaurant")
    #     elif "function" in req_type_lower or "agent_function" in req_type_lower:
    #         agent_manager.user_requirements.main_functions.extend(value.split(", "))
    #         logger.info(f"✅ Added functions: {value}")
    #     elif "tone" in req_type_lower or "personality" in req_type_lower or "agent_tone" in req_type_lower:
    #         agent_manager.user_requirements.tone = value
    #         logger.info(f"✅ Set tone: {value}")
    #     elif "audience" in req_type_lower or "target" in req_type_lower:
    #         agent_manager.user_requirements.target_audience = value
    #         logger.info(f"✅ Set audience: {value}")
    #     elif "hours" in req_type_lower or "operating" in req_type_lower:
    #         agent_manager.user_requirements.special_requirements.append(f"Operating hours: {value}")
    #         logger.info(f"✅ Added hours: {value}")
    #     elif "special" in req_type_lower or "requirement" in req_type_lower:
    #         agent_manager.user_requirements.special_requirements.append(value)
    #         logger.info(f"✅ Added special requirement: {value}")
    #     elif "contact" in req_type_lower:
    #         contact_type = req_type_lower.replace("contact_", "")
    #         agent_manager.user_requirements.contact_info[contact_type] = value
    #         logger.info(f"✅ Added contact info: {contact_type} = {value}")
    #     else:
    #         # Generic storage for any other requirement types
    #         agent_manager.user_requirements.special_requirements.append(f"{requirement_type}: {value}")
    #         logger.info(f"✅ Added generic requirement: {requirement_type} = {value}")

    #     # Log current state of all requirements
    #     logger.info(f"📊 Current requirements summary:")
    #     logger.info(f"   🏢 Business: {agent_manager.user_requirements.business_name}")
    #     logger.info(f"   🏷️ Type: {agent_manager.user_requirements.business_type}")
    #     logger.info(f"   🎯 Functions: {agent_manager.user_requirements.main_functions}")

    #     return f"Stored {requirement_type}: {value}"

    @function_tool
    async def finalize_requirements(self):
        """Finalize requirements and start processing"""
        logger.info("🎯 FINALIZE_REQUIREMENTS called")

        # Check if we have minimum requirements
        # Check if business name is missing
        if not agent_manager.user_requirements.business_name:
            logger.warning("⚠️ No business name stored yet")
            return "I need a bit more information first. What is the name of your business?"

        # Check if business type is missing
        if not agent_manager.user_requirements.business_type:
            logger.warning("⚠️ No business type stored yet")
            return "What type of business would you like to create an agent for?"
    

        logger.info(f"📊 Current requirements: Business={agent_manager.user_requirements.business_name}, Type={agent_manager.user_requirements.business_type}")
        logger.info(f"🎯 Functions: {agent_manager.user_requirements.main_functions}")

        # Start background processing
        logger.info("🚀 Creating processing task...")
        asyncio.create_task(agent_manager.transition_to_processing())

        return "Perfect! I have all the information I need. Give me a few seconds to process everything and create your custom voice AI agent..."

    @function_tool
    async def start_demo(self):
        """Start the demo agent"""
        logger.info(f"🎬 START_DEMO called - Current state: {agent_manager.state}")
        logger.info(f"🔍 Processed spec exists: {agent_manager.processed_spec is not None}")

        if agent_manager.state == AgentState.DEMO_READY:
            logger.info("✅ Triggering demo handoff...")
            asyncio.create_task(agent_manager.handoff_to_demo(agent_manager.room))
            return "Great! Let me connect you to your demo agent now..."
        else:
            logger.warning(f"❌ Demo not ready - State: {agent_manager.state}")
            return "I'm still working on creating your agent. Just a moment more..."
    
    @function_tool
    async def try_demo_again(self):
        """Allow user to try the demo again after feedback"""
        if agent_manager.demo_completed and agent_manager.processed_spec:
            logger.info("Voxie triggering second demo handoff")
            agent_manager.state = AgentState.DEMO_READY  # Reset state for demo
            asyncio.create_task(agent_manager.handoff_to_demo(agent_manager.room))
            return "Perfect! Let me connect you to your updated demo agent now..."
        else:
            return "Let me first process your requirements and create your demo agent."
    
    @function_tool
    async def close_session(self):
        """Close the session gracefully"""
        logger.info("Voxie closing session at user request")
        agent_manager.state = AgentState.COMPLETED
        
        if agent_manager.processed_spec:
            business_name = agent_manager.processed_spec.business_context.get("business_name", "your business")
            return f"Thank you for using Voxie to create your custom voice AI agent for {business_name}! Your agent specifications have been saved and you can come back anytime to test or make changes. Have a wonderful day!"
        else:
            return "Thank you for using Voxie! Feel free to come back anytime when you're ready to create your custom voice AI agent. Have a great day!"
    
    @function_tool
    async def ask_demo_preference(self):
        """Ask user if they want to try the demo or are satisfied"""
        logger.info(f"🤔 ASK_DEMO_PREFERENCE called - Demo completed: {agent_manager.demo_completed}")
        if agent_manager.demo_completed:
            return "Would you like to try the demo again with any updates, or are you satisfied with your agent? If you're all set, just let me know and I can close our session for you."
        else:
            return "Your agent is ready! Would you like to try the demo now, or do you have any questions first?"

    @function_tool
    async def check_processing_status(self):
        """Check the current processing status"""
        logger.info(f"📋 CHECK_PROCESSING_STATUS called - Current state: {agent_manager.state}")

        if agent_manager.state == AgentState.PROCESSING:
            return "I'm still working on creating your agent. It should be ready in just a few more moments. I'm configuring all the features you requested!"
        elif agent_manager.state == AgentState.DEMO_READY:
            return "Great news! Your agent is ready to test. Would you like to try it out now?"
        elif agent_manager.state == AgentState.DEMO_ACTIVE:
            return "You're currently testing your demo agent. When you're done, just ask to speak with me again!"
        else:
            return "I'm here to help you create your custom agent. What type of business agent would you like to create?"

    @function_tool
    async def engage_user_during_wait(self):
        """Keep user engaged while processing"""
        logger.info("💬 ENGAGE_USER_DURING_WAIT called")
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
            "voice": "alloy",  # Different from Voxie's coral
            "tone": "friendly and welcoming",
            "functions": ["take_reservation", "menu_inquiry", "take_order"],
            "sample_responses": [
                "Thank you for calling {business_name}! How can I help you today?",
                "I'd be happy to help you make a reservation.",
                "Let me check our menu for you."
            ]
        },
        "dental": {
            "voice": "nova",  # Different from Voxie's coral
            "tone": "professional and reassuring",
            "functions": ["schedule_appointment", "check_insurance", "emergency_info"],
            "sample_responses": [
                "Thank you for calling {business_name}. How may I assist you today?",
                "I can help you schedule an appointment.",
                "Let me check your insurance coverage."
            ]
        },
        "pizza": {
            "voice": "echo",  # Different from Voxie's coral
            "tone": "casual and enthusiastic", 
            "functions": ["take_order", "menu_inquiry", "take_reservation"],
            "sample_responses": [
                "Hey there! Welcome to {business_name}! Ready to order some amazing pizza?",
                "What can I get started for you today?",
                "Let me tell you about our daily specials!"
            ]
        },
        "retail": {
            "voice": "alloy",  # Different from Voxie's coral
            "tone": "helpful and professional",
            "functions": ["check_product_availability", "store_hours"],
            "sample_responses": [
                "Hello and welcome to {business_name}! How can I help you today?",
                "I can help you find what you're looking for.",
                "Let me check if we have that in stock for you."
            ]
        },
        "medical": {
            "voice": "nova",  # Different from Voxie's coral
            "tone": "caring and professional", 
            "functions": ["schedule_appointment", "check_insurance", "emergency_info"],
            "sample_responses": [
                "Thank you for calling {business_name}. How may I help you today?",
                "I can assist you with scheduling an appointment.",
                "Let me help you with your medical needs."
            ]
        },
        "general": {
            "voice": "alloy",  # Different from Voxie's coral
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
        logger.info("🏭 Processing user requirements...")
        logger.info(f"📋 Business type: {requirements.business_type}")
        logger.info(f"🏢 Business name: {requirements.business_name}")
        logger.info(f"🎯 Functions: {requirements.main_functions}")

        # Simulate processing time with progress updates
        logger.info("⏳ Processing step 1/3: Analyzing business type...")
        await asyncio.sleep(2)

        # Determine business type from requirements
        business_type = "general"  # Default
        if requirements.business_type:
            btype_lower = requirements.business_type.lower()
            logger.info(f"🔍 Analyzing business type: '{btype_lower}'")
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

        logger.info(f"✅ Determined business type: {business_type}")

        logger.info("⏳ Processing step 2/3: Building agent specification...")
        await asyncio.sleep(2)

        template = self.BUSINESS_TEMPLATES.get(business_type, self.BUSINESS_TEMPLATES["general"])
        logger.info(f"📋 Using template: {business_type} with voice: {template['voice']}")

        # Build agent specification
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

        logger.info("⏳ Processing step 3/3: Finalizing configuration...")
        await asyncio.sleep(1)

        logger.info(f"🎉 Generated spec for {spec.agent_type}")
        logger.info(f"🎵 Voice: {spec.voice}")
        logger.info(f"🛠️ Functions: {len(spec.functions)} configured")
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
        
        # Add template functions
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


class DemoAgentCreator:
    """Creates demo agents from processed specifications"""
    
    @staticmethod
    def create_agent(spec: ProcessedAgentSpec) -> Agent:
        """Create a demo agent from the specification"""
        logger.info(f"Creating demo agent: {spec.agent_type}")
        
        # Get business type to determine which agent class to create
        business_type = spec.business_context.get("business_type", "general")
        
        if "restaurant" in business_type.lower() or "pizza" in business_type.lower():
            return DemoAgentCreator._create_restaurant_agent(spec)
        elif "dental" in business_type.lower() or "medical" in business_type.lower():
            return DemoAgentCreator._create_medical_agent(spec)
        elif "retail" in business_type.lower():
            return DemoAgentCreator._create_retail_agent(spec)
        else:
            return DemoAgentCreator._create_general_agent(spec)
    
    @staticmethod
    def _create_restaurant_agent(spec: ProcessedAgentSpec):
        """Create restaurant-specific demo agent"""
        class RestaurantDemoAgent(Agent):
            def __init__(self):
                super().__init__(instructions=spec.instructions)

            @function_tool
            async def take_reservation(self, date: str, time: str, party_size: str, name: str, phone: str = ""):
                """Take a restaurant reservation"""
                business_name = spec.business_context.get("business_name", "our restaurant")
                logger.info(f"Demo agent taking reservation: {name} for {party_size} people on {date} at {time}")
                return f"Perfect! I've made a reservation at {business_name} for {name} for {party_size} people on {date} at {time}. We'll see you then!"

            @function_tool
            async def menu_inquiry(self, item: str = ""):
                """Handle menu inquiries"""
                logger.info(f"Demo agent handling menu inquiry for: {item}")
                if item:
                    return f"Great choice! Our {item} is one of our most popular dishes. It's made with fresh ingredients and comes with a side of your choice."
                else:
                    return f"We have a wonderful menu. What would you like to know more about?"

            @function_tool
            async def take_order(self, items: str, customer_name: str, phone: str = "", address: str = ""):
                """Take a food order"""
                business_name = spec.business_context.get("business_name", "our restaurant")
                logger.info(f"Demo agent taking order: {items} for {customer_name}")
                return f"Excellent! I've got your order for {items}. That'll be ready in about 25-30 minutes at {business_name}. Thank you!"

            # KNOWLEDGE BASE TOOLS - Available to all restaurant agents
            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base for information"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer to a specific question from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get technical specifications for a specific product"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)
                
            @function_tool
            async def end_demo(self):
                """End the demo session"""
                return "Thank you for trying out the demo! This gives you an idea of how your custom voice agent would work. Would you like to speak with Voxie again to make adjustments or discuss next steps?"
            
            @function_tool
            async def handoff_to_voxie(self):
                """Handoff back to Voxie for feedback"""
                logger.info("Demo agent requesting handoff back to Voxie")
                # Trigger handoff in manager
                asyncio.create_task(agent_manager.handoff_back_to_voxie(agent_manager.room))
                return "Let me connect you back to Voxie now..."
        
        return RestaurantDemoAgent()
    
    @staticmethod
    def _create_medical_agent(spec: ProcessedAgentSpec):
        """Create medical/dental-specific demo agent"""
        class MedicalDemoAgent(Agent):
            def __init__(self):
                super().__init__(instructions=spec.instructions)
                
            @function_tool
            async def schedule_appointment(self, date: str, time: str, patient_name: str, phone: str, service_type: str = "consultation"):
                """Schedule a medical/dental appointment"""
                business_name = spec.business_context.get("business_name", "our facility")
                logger.info(f"Demo agent scheduling appointment: {patient_name} on {date} at {time}")
                return f"I've scheduled your {service_type} appointment at {business_name} for {patient_name} on {date} at {time}. We'll send you a confirmation shortly."
            
            @function_tool
            async def check_insurance(self, insurance_provider: str, member_id: str = ""):
                """Check insurance coverage"""
                logger.info(f"Demo agent checking insurance: {insurance_provider}")
                return f"I can help you verify your {insurance_provider} coverage. We are in-network with most major providers. Let me check your benefits."
            
            @function_tool
            async def emergency_info(self):
                """Provide emergency contact information"""
                return "For emergencies outside business hours, please call our emergency line. If this is a medical emergency, please call 911 immediately."

            # KNOWLEDGE BASE TOOLS - Available to all medical agents
            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base for information"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer to a specific question from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get technical specifications for a specific product"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)
                
            @function_tool
            async def end_demo(self):
                """End the demo session"""
                return "Thank you for trying out the demo! This gives you an idea of how your custom voice agent would work. Would you like to speak with Voxie again to make adjustments or discuss next steps?"
            
            @function_tool
            async def handoff_to_voxie(self):
                """Handoff back to Voxie for feedback"""
                logger.info("Demo agent requesting handoff back to Voxie")
                # Trigger handoff in manager
                asyncio.create_task(agent_manager.handoff_back_to_voxie(agent_manager.room))
                return "Let me connect you back to Voxie now..."
        
        return MedicalDemoAgent()
    
    @staticmethod
    def _create_retail_agent(spec: ProcessedAgentSpec):
        """Create retail-specific demo agent"""
        class RetailDemoAgent(Agent):
            def __init__(self):
                super().__init__(instructions=spec.instructions)
                
            @function_tool
            async def check_product_availability(self, product_name: str):
                """Check if a product is in stock"""
                logger.info(f"Demo agent checking product availability: {product_name}")
                return f"Let me check our inventory for {product_name}. Yes, we have that in stock! Would you like me to hold one for you?"
            
            @function_tool
            async def store_hours(self):
                """Provide store hours"""
                return "We're open Monday through Saturday 9 AM to 8 PM, and Sunday 11 AM to 6 PM."
                
            @function_tool
            async def end_demo(self):
                """End the demo session"""
                return "Thank you for trying out the demo! This gives you an idea of how your custom voice agent would work. Would you like to speak with Voxie again to make adjustments or discuss next steps?"
            
            @function_tool
            async def handoff_to_voxie(self):
                """Handoff back to Voxie for feedback"""
                logger.info("Demo agent requesting handoff back to Voxie")
                # Trigger handoff in manager
                asyncio.create_task(agent_manager.handoff_back_to_voxie(agent_manager.room))
                return "Let me connect you back to Voxie now..."
        
        return RetailDemoAgent()
    
    @staticmethod
    def _create_general_agent(spec: ProcessedAgentSpec):
        """Create general business demo agent"""
        class GeneralDemoAgent(Agent):
            def __init__(self):
                super().__init__(instructions=spec.instructions)
                
            @function_tool
            async def general_inquiry(self, topic: str, customer_name: str = ""):
                """Handle general business inquiries"""
                business_name = spec.business_context.get("business_name", "our business")
                logger.info(f"Demo agent handling general inquiry: {topic}")
                return f"Thank you for contacting {business_name}! I'd be happy to help you with {topic}. Let me provide you with that information."
            
            @function_tool
            async def business_hours(self):
                """Provide business hours"""
                return "We're typically open Monday through Friday 9 AM to 5 PM. Would you like me to check our specific hours for today?"

            # KNOWLEDGE BASE TOOLS - Available to all general agents (including car dealerships)
            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base for information"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer to a specific question from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get technical specifications for a specific product"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)
                
            @function_tool
            async def end_demo(self):
                """End the demo session"""
                return "Thank you for trying out the demo! This gives you an idea of how your custom voice agent would work. Would you like to speak with Voxie again to make adjustments or discuss next steps?"
            
            @function_tool
            async def handoff_to_voxie(self):
                """Handoff back to Voxie for feedback"""
                logger.info("Demo agent requesting handoff back to Voxie")
                # Trigger handoff in manager
                asyncio.create_task(agent_manager.handoff_back_to_voxie(agent_manager.room))
                return "Let me connect you back to Voxie now..."
        
        return GeneralDemoAgent()


async def entrypoint(ctx: agents.JobContext):
    """Main entry point - starts with Voxie agent"""
    logger.info("Starting multi-agent system with Voxie")
    
    # Store room and context reference for handoffs
    agent_manager.room = ctx.room
    agent_manager.context = ctx
    
    # Start with Voxie agent
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="marin")  # Voxie's voice
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