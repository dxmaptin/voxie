"""
Knowledge Base Tools for Voice Agents
This module provides function tools that agents can use to access the Ragie knowledge base
"""

import sys
import os

# Add the function_call directory to the path so we can import ragie modules
current_dir = os.path.dirname(os.path.abspath(__file__))
function_call_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'function_call')
sys.path.append(function_call_dir)

from livekit.agents.llm import function_tool
from ragie_db_tool import search_ragie_knowledge, ragie_kb
from ragie_voice_agent import answer_question
import logging

logger = logging.getLogger("knowledge-base-tools")

class KnowledgeBaseTools:
    """Collection of function tools for accessing knowledge base"""

    @staticmethod
    @function_tool
    async def search_knowledge_base(query: str, max_results: int = 3):
        """
        Search the company knowledge base for information
        Use this when customers ask questions about products, policies, or company information
        """
        try:
            logger.info(f"Knowledge base search: {query}")

            # Use the Ragie search function
            results = search_ragie_knowledge(query, max_results)

            if not results:
                return "I don't have specific information about that in my knowledge base. Is there something else I can help you with?"

            # Format results for conversational response
            if len(results) == 1:
                content = results[0].get('content', '')
                # Truncate for voice response
                summary = content[:300] + "..." if len(content) > 300 else content
                return f"Based on my knowledge base: {summary}"
            else:
                # Multiple results - combine top 2
                combined_info = ""
                for i, result in enumerate(results[:2]):
                    content = result.get('content', '')
                    summary = content[:150] + "..." if len(content) > 150 else content
                    combined_info += f"{summary} "

                return f"Here's what I found in my knowledge base: {combined_info}"

        except Exception as e:
            logger.error(f"Knowledge base search error: {e}")
            return "I'm having trouble accessing my knowledge base right now. Can I help you with something else?"

    @staticmethod
    @function_tool
    async def answer_detailed_question(question: str):
        """
        Get a detailed answer to a specific question from the knowledge base
        Use this for complex questions that need comprehensive answers
        """
        try:
            logger.info(f"Detailed knowledge question: {question}")

            # Use the answer_question function from ragie_voice_agent
            answer = answer_question(question)
            return answer

        except Exception as e:
            logger.error(f"Detailed question error: {e}")
            return "I'm sorry, I couldn't find detailed information about that. Could you try asking a different question?"

    @staticmethod
    @function_tool
    async def get_product_specifications(product_name: str):
        """
        Get technical specifications for a specific product
        Use this when customers ask about specs, features, or technical details
        """
        try:
            logger.info(f"Product specs search: {product_name}")

            # Search for specifications
            spec_query = f"{product_name} specifications features technical details"
            results = search_ragie_knowledge(spec_query, 2)

            if not results:
                return f"I don't have specific specifications for {product_name} in my knowledge base."

            # Look for specification-related content
            spec_content = ""
            for result in results:
                content = result.get('content', '')
                if any(word in content.lower() for word in ['spec', 'feature', 'technical', 'performance', 'capability']):
                    spec_content += content[:200] + "... "

            if spec_content:
                return f"Here are the specifications for {product_name}: {spec_content}"
            else:
                # Fallback to general content
                general_content = results[0].get('content', '')[:250]
                return f"Here's information about {product_name}: {general_content}..."

        except Exception as e:
            logger.error(f"Product specs error: {e}")
            return f"I'm having trouble finding specifications for {product_name} right now."

    @staticmethod
    @function_tool
    async def check_knowledge_availability():
        """
        Check if the knowledge base is available and what document is loaded
        Use this to verify knowledge base status
        """
        try:
            doc_info = ragie_kb.get_document_info()
            if doc_info:
                doc_name = doc_info.get('name', 'Unknown document')
                return f"My knowledge base is available and contains information from: {doc_name}"
            else:
                return "My knowledge base is currently unavailable."
        except Exception as e:
            logger.error(f"Knowledge availability check error: {e}")
            return "I'm having trouble checking my knowledge base status."

# Export the tools for easy import
knowledge_tools = [
    KnowledgeBaseTools.search_knowledge_base,
    KnowledgeBaseTools.answer_detailed_question,
    KnowledgeBaseTools.get_product_specifications,
    KnowledgeBaseTools.check_knowledge_availability
]

# Test the tools if run directly
if __name__ == "__main__":
    import asyncio

    async def test_tools():
        print("🧪 Testing knowledge base tools...")

        # Test basic search
        result1 = await KnowledgeBaseTools.search_knowledge_base("EX5 features")
        print(f"Basic search: {result1[:100]}...")

        # Test detailed question
        result2 = await KnowledgeBaseTools.answer_detailed_question("What is the EX5?")
        print(f"Detailed question: {result2[:100]}...")

        # Test specifications
        result3 = await KnowledgeBaseTools.get_product_specifications("EX5")
        print(f"Specifications: {result3[:100]}...")

        # Test availability
        result4 = await KnowledgeBaseTools.check_knowledge_availability()
        print(f"Availability: {result4}")

    asyncio.run(test_tools())