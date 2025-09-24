"""
Simplified Ragie-only voice agent integration
This replaces the complex FAISS setup with pure Ragie knowledge base access
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from ragie_db_tool import search_ragie_knowledge, ragie_kb

# -------------------------
# Setup
# -------------------------
load_dotenv()

# Test Ragie connection
try:
    test_ragie = ragie_kb.get_document_info()
    print("✅ Ragie knowledge base connected successfully")
    print(f"📄 Document: {test_ragie.get('name', 'Unknown')}")
except Exception as e:
    print(f"❌ Error connecting to Ragie: {e}")

# -------------------------
# Helper Functions
# -------------------------
def extract_keywords(query: str) -> List[str]:
    """Extract meaningful keywords from user query"""
    # Remove common filler words
    stop_words = {'i', 'want', 'need', 'looking', 'for', 'a', 'an', 'the', 'with', 'good', 'best', 'some', 'what', 'is', 'are', 'how', 'can', 'could', 'would', 'should'}

    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords

def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, any]:
    """
    Main search function - queries Ragie knowledge base
    This replaces the old product database search
    """
    print(f"\n🔎 Searching knowledge base for: '{query}'")

    keywords = extract_keywords(query)
    print(f"🏷️  Keywords: {keywords}")

    if not query.strip():
        return {
            "success": False,
            "message": "Please provide a search query.",
            "results": []
        }

    try:
        # Query Ragie knowledge base
        ragie_results = search_ragie_knowledge(query, max_results)

        if not ragie_results:
            return {
                "success": False,
                "message": "No information found in knowledge base. Try rephrasing your question.",
                "results": []
            }

        # Format results for the voice agent
        formatted_results = []
        for item in ragie_results:
            formatted_results.append({
                "content": item.get('content', ''),
                "summary": item.get('content', '')[:200] + '...' if len(item.get('content', '')) > 200 else item.get('content', ''),
                "relevance": f"{item.get('score', 0):.2f}",
                "source": "Knowledge Base",
                "metadata": item.get('metadata', {})
            })

        return {
            "success": True,
            "message": f"Found {len(formatted_results)} relevant pieces of information in the knowledge base.",
            "results": formatted_results,
            "search_info": {
                "query": query,
                "keywords": keywords,
                "document_source": "Ragie Knowledge Base"
            }
        }

    except Exception as e:
        print(f"❌ Search error: {e}")
        return {
            "success": False,
            "message": f"Search failed: {str(e)}",
            "results": []
        }

def answer_question(question: str) -> str:
    """
    Generate a conversational answer from knowledge base search
    This is what the voice agent will use
    """
    search_result = search_knowledge_base(question, 3)

    if not search_result["success"]:
        return "I'm sorry, I couldn't find information about that in my knowledge base. Could you try asking a different question?"

    # Combine the top results into a coherent answer
    results = search_result["results"]

    if len(results) == 1:
        return f"Based on my knowledge base: {results[0]['summary']}"
    else:
        answer = "Based on my knowledge base, here's what I found: "
        for i, result in enumerate(results[:2]):  # Use top 2 results
            answer += f"{result['summary']} "

        return answer

# -------------------------
# Voice Agent Functions
# -------------------------
def handle_voice_query(user_input: str) -> Dict[str, str]:
    """
    Main function for voice agent to handle user queries
    Returns structured response for the voice agent
    """

    # Determine query type and generate response
    if any(word in user_input.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
        # Question - search knowledge base
        answer = answer_question(user_input)
        return {
            "type": "knowledge_response",
            "message": answer,
            "source": "ragie_knowledge_base"
        }
    else:
        # General query - still search knowledge base
        search_result = search_knowledge_base(user_input)

        if search_result["success"] and search_result["results"]:
            return {
                "type": "search_response",
                "message": f"I found information about that: {search_result['results'][0]['summary']}",
                "source": "ragie_knowledge_base"
            }
        else:
            return {
                "type": "no_results",
                "message": "I don't have specific information about that in my knowledge base. Is there something else I can help you with?",
                "source": "fallback"
            }

# -------------------------
# Test Functions
# -------------------------
if __name__ == "__main__":
    print("🧪 Testing Ragie voice agent integration...")

    # Test queries for the Geely EX5 document
    test_queries = [
        "What is the EX5?",
        "Tell me about features",
        "What are the specifications?",
        "How much does it cost?",
        "What are the safety features?"
    ]

    for query in test_queries:
        print(f"\n" + "="*60)
        print(f"🎤 User Query: {query}")

        response = handle_voice_query(query)

        print(f"🤖 Bot Response Type: {response['type']}")
        print(f"💬 Bot Message: {response['message'][:200]}...")
        print(f"📋 Source: {response['source']}")