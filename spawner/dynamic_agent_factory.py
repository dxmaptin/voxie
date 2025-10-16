"""
Dynamic Agent Factory - Creates LiveKit agents dynamically from database configs
"""

import logging
import sys
import os
import asyncio
from typing import Dict, Any
from livekit.agents import Agent
from livekit.agents.llm import function_tool

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'voxie-test', 'src'))

from knowledge_base_tools import KnowledgeBaseTools

logger = logging.getLogger("agent-factory")


class DynamicAgentFactory:
    """Creates agents dynamically from database configurations"""

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Agent:
        """
        Create a LiveKit Agent from a database configuration

        Args:
            config: Agent configuration from AgentLoader

        Returns:
            Configured Agent instance
        """
        logger.info(f"🏭 Creating dynamic agent: {config['name']}")
        logger.info(f"   Instructions length: {len(config['instructions'])} chars")
        logger.info(f"   Functions: {len(config['functions'])}")
        logger.info(f"   Business type: {config['business_context'].get('business_type')}")

        # Determine agent type based on business context
        business_type = config['business_context'].get('business_type', 'general')

        # Create appropriate agent class
        if 'restaurant' in business_type.lower() or 'pizza' in business_type.lower():
            return DynamicAgentFactory._create_restaurant_agent(config)
        elif 'dental' in business_type.lower() or 'medical' in business_type.lower():
            return DynamicAgentFactory._create_medical_agent(config)
        elif 'retail' in business_type.lower() or 'store' in business_type.lower():
            return DynamicAgentFactory._create_retail_agent(config)
        else:
            return DynamicAgentFactory._create_general_agent(config)

    @staticmethod
    def _create_restaurant_agent(config: Dict[str, Any]) -> Agent:
        """Create restaurant/food service agent"""

        class DynamicRestaurantAgent(Agent):
            def __init__(self):
                super().__init__(instructions=config['instructions'])
                self.config = config

            @function_tool
            async def take_reservation(self, date: str, time: str, party_size: str, name: str, phone: str = ""):
                """Take a restaurant reservation"""
                business_name = self.config['business_context'].get('business_name', 'our restaurant')
                logger.info(f"📅 Reservation: {name} for {party_size} on {date} at {time}")
                return f"Perfect! I've made a reservation at {business_name} for {name} for {party_size} people on {date} at {time}. We'll see you then!"

            @function_tool
            async def menu_inquiry(self, item: str = ""):
                """Handle menu inquiries"""
                logger.info(f"📋 Menu inquiry: {item}")
                if item:
                    return f"Great choice! Our {item} is one of our most popular dishes. It's made with fresh ingredients and comes with a side of your choice."
                else:
                    return "We have a wonderful menu. What would you like to know more about?"

            @function_tool
            async def take_order(self, items: str, customer_name: str = "", phone: str = "", address: str = ""):
                """Take a food order"""
                business_name = self.config['business_context'].get('business_name', 'our restaurant')
                logger.info(f"🍕 Order: {items} for {customer_name}")
                return f"Excellent! I've got your order for {items}. That'll be ready in about 25-30 minutes at {business_name}. Thank you!"

            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get product specifications"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)

        logger.info("✅ Created restaurant agent")
        return DynamicRestaurantAgent()

    @staticmethod
    def _create_medical_agent(config: Dict[str, Any]) -> Agent:
        """Create medical/dental agent"""

        class DynamicMedicalAgent(Agent):
            def __init__(self):
                super().__init__(instructions=config['instructions'])
                self.config = config

            @function_tool
            async def schedule_appointment(self, date: str, time: str, patient_name: str, phone: str, service_type: str = "consultation"):
                """Schedule a medical/dental appointment"""
                business_name = self.config['business_context'].get('business_name', 'our facility')
                logger.info(f"🏥 Appointment: {patient_name} on {date} at {time}")
                return f"I've scheduled your {service_type} appointment at {business_name} for {patient_name} on {date} at {time}. We'll send you a confirmation shortly."

            @function_tool
            async def check_insurance(self, insurance_provider: str, member_id: str = ""):
                """Check insurance coverage"""
                logger.info(f"💳 Insurance check: {insurance_provider}")
                return f"I can help you verify your {insurance_provider} coverage. We are in-network with most major providers. Let me check your benefits."

            @function_tool
            async def emergency_info(self):
                """Provide emergency contact information"""
                return "For emergencies outside business hours, please call our emergency line. If this is a medical emergency, please call 911 immediately."

            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get product specifications"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)

        logger.info("✅ Created medical agent")
        return DynamicMedicalAgent()

    @staticmethod
    def _create_retail_agent(config: Dict[str, Any]) -> Agent:
        """Create retail/store agent"""

        class DynamicRetailAgent(Agent):
            def __init__(self):
                super().__init__(instructions=config['instructions'])
                self.config = config

            @function_tool
            async def check_product_availability(self, product_name: str):
                """Check if a product is in stock"""
                logger.info(f"📦 Product check: {product_name}")
                return f"Let me check our inventory for {product_name}. Yes, we have that in stock! Would you like me to hold one for you?"

            @function_tool
            async def store_hours(self):
                """Provide store hours"""
                return "We're open Monday through Saturday 9 AM to 8 PM, and Sunday 11 AM to 6 PM."

            @function_tool
            async def search_knowledge_base(self, query: str, max_results: int = 3):
                """Search the company knowledge base"""
                return await KnowledgeBaseTools.search_knowledge_base(query, max_results)

            @function_tool
            async def answer_detailed_question(self, question: str):
                """Get a detailed answer from the knowledge base"""
                return await KnowledgeBaseTools.answer_detailed_question(question)

            @function_tool
            async def get_product_specifications(self, product_name: str):
                """Get product specifications"""
                return await KnowledgeBaseTools.get_product_specifications(product_name)

        logger.info("✅ Created retail agent")
        return DynamicRetailAgent()

    @staticmethod
    def _create_general_agent(config: Dict[str, Any]) -> Agent:
        """Create general business agent (fallback for all other types)"""

        class DynamicGeneralAgent(Agent):
            def __init__(self):
                super().__init__(instructions=config['instructions'])
                self.config = config

            @function_tool
            async def general_inquiry(self, topic: str, customer_name: str = ""):
                """Handle general business inquiries"""
                business_name = self.config['business_context'].get('business_name', 'our business')
                logger.info(f"💼 General inquiry: {topic}")
                return f"Thank you for contacting {business_name}! I'd be happy to help you with {topic}. Let me provide you with that information."

            @function_tool
            async def business_hours(self):
                """Provide business hours"""
                return "We're typically open Monday through Friday 9 AM to 5 PM. Would you like me to check our specific hours for today?"

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

        logger.info("✅ Created general agent")
        return DynamicGeneralAgent()
