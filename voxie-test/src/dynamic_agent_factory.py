"""
spawner/dynamic_agent_factory.py
Constructs demo agents dynamically from config
"""
import logging
from typing import Any, Dict, List
from livekit.agents import Agent
from livekit.agents.llm import function_tool
from knowledge_base_tools import KnowledgeBaseTools
from agent_loader import AgentConfigData

logger = logging.getLogger("spawner-factory")


class DynamicAgentFactory:
    """Dynamically creates agents from configuration"""
    
    @staticmethod
    def create_agent(config: AgentConfigData) -> Agent:
        """
        Create a demo agent from loaded configuration
        
        Uses the prompt_text or instructions_override as agent instructions
        Creates a generic agent that can be used for any prompt
        """
        logger.info(f"Creating agent from config: {config.name}")
        
        # Get instructions - prefer override if available
        instructions = config.instructions_override or config.prompt_text
        if not instructions:
            logger.warning(f"No instructions found for agent {config.id}")
            instructions = f"You are {config.name}. {config.tagline}"
        
        class ConfiguredDemoAgent(Agent):
            def __init__(self, cfg: AgentConfigData):
                self.config = cfg
                super().__init__(instructions=instructions)
            
            @function_tool
            async def end_demo(self):
                """End the demo session"""
                return "Thank you for testing this agent! Feel free to return to the dashboard for feedback or adjustments."
        
        # Create instance with config
        agent = ConfiguredDemoAgent(config)
        
        logger.info(f"Agent '{config.name}' created successfully with voice: {config.voice}")
        return agent