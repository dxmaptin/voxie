import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import re
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import openai
from rag_db_tool import PRODUCT_DATABASE, embed_text, load_index_and_mapping
from ragie_db_tool import search_ragie_knowledge, ragie_kb

# -------------------------
# Setup
# -------------------------
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load FAISS index (keep for local products)
try:
    index, id_to_product = load_index_and_mapping()
    print("✅ Local database loaded successfully")
except Exception as e:
    print(f"❌ Error loading local database: {e}")
    index, id_to_product = None, {}

# Test Ragie connection
try:
    test_ragie = ragie_kb.get_document_info()
    print("✅ Ragie knowledge base connected successfully")
except Exception as e:
    print(f"❌ Error connecting to Ragie: {e}")

# -------------------------
# Enhanced Helper Functions
# -------------------------
def extract_budget_from_query(query: str) -> Optional[Tuple[float, float]]:
    """Extract budget from user query with better parsing"""
    query_lower = query.lower().strip()

    # Remove common words that might interfere
    query_lower = re.sub(r'\b(want|need|looking|for|a|an|the)\b', ' ', query_lower)

    # Under/below patterns
    under_match = re.search(r'under\s*\$?(\d+)', query_lower)
    below_match = re.search(r'below\s*\$?(\d+)', query_lower)
    if under_match or below_match:
        amount = float(under_match.group(1) if under_match else below_match.group(1))
        return (0, amount)

    # Above/over patterns
    above_match = re.search(r'above\s*\$?(\d+)', query_lower)
    over_match = re.search(r'over\s*\$?(\d+)', query_lower)
    if above_match or over_match:
        amount = float(above_match.group(1) if above_match else over_match.group(1))
        return (amount, 10000)

    # Range patterns: $100-300, $100 to $300, between $100 and $300
    range_patterns = [
        r'\$?(\d+)\s*[-–—to]\s*\$?(\d+)',
        r'between\s*\$?(\d+)\s*and\s*\$?(\d+)',
        r'\$?(\d+)\s*-\s*\$?(\d+)'
    ]

    for pattern in range_patterns:
        match = re.search(pattern, query_lower)
        if match:
            min_price, max_price = float(match.group(1)), float(match.group(2))
            return (min(min_price, max_price), max(min_price, max_price))

    # Single price (assume max budget)
    single_price = re.search(r'\$(\d+)(?!\s*[-–—to])', query_lower)
    if single_price:
        return (0, float(single_price.group(1)))

    return None

def get_price_value(price_str: str) -> float:
    """Convert price string to numeric value with better error handling"""
    if not price_str:
        return 0
    try:
        # Handle different price formats: $299, $1,299.99, 299.99, etc.
        cleaned = re.sub(r'[^\d.,]', '', str(price_str))
        # Remove commas (thousands separator)
        cleaned = cleaned.replace(',', '')
        return float(cleaned) if cleaned else 0
    except (ValueError, TypeError):
        return 0

def extract_product_keywords(query: str) -> List[str]:
    """Extract meaningful product keywords from query"""
    # Remove budget-related phrases first
    cleaned_query = re.sub(r'under \$?\d+|above \$?\d+|below \$?\d+|\$\d+[-–—\d]*|between.+and.+\d+', '', query.lower())

    # Remove common filler words
    stop_words = {'i', 'want', 'need', 'looking', 'for', 'a', 'an', 'the', 'with', 'good', 'best', 'some'}

    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', cleaned_query)
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords

def hybrid_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    NEW: Hybrid search combining local products + Ragie knowledge base
    This replaces the old product-only search
    """
    results = []

    # 1. Search local products (existing functionality)
    local_results = search_local_products(query, max_results // 2)
    for item in local_results:
        item['source'] = 'local_products'
        results.append(item)

    # 2. Search Ragie knowledge base (NEW)
    try:
        ragie_results = search_ragie_knowledge(query, max_results // 2)
        for item in ragie_results:
            # Transform Ragie results to match product format
            formatted_item = {
                'id': item.get('id', 'ragie_' + str(len(results))),
                'name': item.get('summary', 'Knowledge Base Result')[:50],
                'description': item.get('content', '')[:200] + '...',
                'content': item.get('content', ''),
                'score': item.get('score', 0.0),
                'source': 'ragie_knowledge',
                'metadata': item.get('metadata', {})
            }
            results.append(formatted_item)
    except Exception as e:
        print(f"⚠️  Ragie search failed, using local only: {e}")

    # Sort by relevance score if available
    results.sort(key=lambda x: x.get('score', 0.0), reverse=True)

    return results[:max_results]

def search_local_products(query: str, max_results: int = 5) -> List[Dict]:
    """
    Original product search function (kept for local products)
    """
    if not index or not id_to_product:
        return []

    try:
        # Get query embedding
        query_embedding = embed_text(query).reshape(1, -1)

        # Search FAISS index
        scores, indices = index.search(query_embedding, max_results)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in id_to_product:
                product = id_to_product[idx].copy()
                product['score'] = float(score)
                results.append(product)

        return results
    except Exception as e:
        print(f"❌ Error in local search: {e}")
        return []

def smart_product_search(query: str, budget_range: Optional[Tuple[float, float]] = None) -> List[Dict]:
    """
    UPDATED: Main search function now uses hybrid search
    """
    print(f"🔍 Searching for: '{query}' with budget: {budget_range}")

    # Use hybrid search instead of local-only
    candidates = hybrid_search(query, 10)

    if not candidates:
        return []

    # Apply budget filtering (only for local products that have prices)
    if budget_range:
        min_budget, max_budget = budget_range
        filtered_candidates = []

        for product in candidates:
            # Only filter products with price info (local products)
            if product.get('source') == 'local_products' and 'price' in product:
                price = get_price_value(product['price'])
                if min_budget <= price <= max_budget:
                    filtered_candidates.append(product)
            else:
                # Include Ragie results regardless of budget (they might not have price info)
                filtered_candidates.append(product)

        candidates = filtered_candidates

    return candidates[:5]  # Return top 5 results

# -------------------------
# Main Search Function (Updated)
# -------------------------
def search_products_with_ai(user_query: str) -> Dict[str, any]:
    """
    UPDATED: Enhanced product search with Ragie integration
    """
    print(f"\n🔎 Processing query: '{user_query}'")

    # Extract budget and keywords
    budget_range = extract_budget_from_query(user_query)
    keywords = extract_product_keywords(user_query)

    print(f"💰 Budget range: {budget_range}")
    print(f"🏷️  Keywords: {keywords}")

    if not user_query.strip():
        return {
            "success": False,
            "message": "Please provide a search query.",
            "results": []
        }

    try:
        # Use updated search function
        results = smart_product_search(user_query, budget_range)

        if not results:
            return {
                "success": False,
                "message": "No products found matching your criteria. Try a different search term or budget range.",
                "results": []
            }

        # Format results for the voice agent
        formatted_results = []
        for product in results:
            if product.get('source') == 'ragie_knowledge':
                # Format Ragie results
                formatted_results.append({
                    "name": product.get('name', 'Knowledge Base Result'),
                    "info": product.get('content', '')[:300] + '...',
                    "source": "Knowledge Base",
                    "relevance": f"{product.get('score', 0):.2f}"
                })
            else:
                # Format local product results
                formatted_results.append({
                    "name": product.get('name', 'Unknown'),
                    "price": product.get('price', 'Price not available'),
                    "description": product.get('description', ''),
                    "rating": product.get('rating', 'Not rated'),
                    "source": "Product Catalog"
                })

        return {
            "success": True,
            "message": f"Found {len(formatted_results)} results combining product catalog and knowledge base.",
            "results": formatted_results,
            "search_info": {
                "query": user_query,
                "budget_range": budget_range,
                "keywords": keywords,
                "total_sources": len(set(r.get('source', '') for r in results))
            }
        }

    except Exception as e:
        print(f"❌ Search error: {e}")
        return {
            "success": False,
            "message": f"Search failed: {str(e)}",
            "results": []
        }

# -------------------------
# Test Functions
# -------------------------
if __name__ == "__main__":
    print("🧪 Testing hybrid search system...")

    # Test queries
    test_queries = [
        "smartphone under $800",
        "what is machine learning?",  # Should hit Ragie
        "laptop for programming",
        "company policies"  # Should hit Ragie
    ]

    for query in test_queries:
        print(f"\n" + "="*50)
        result = search_products_with_ai(query)
        print(f"Query: {query}")
        print(f"Success: {result['success']}")
        print(f"Results: {len(result['results'])}")
        if result['results']:
            for i, res in enumerate(result['results'][:2]):  # Show first 2
                print(f"  {i+1}. {res.get('name', 'N/A')} (Source: {res.get('source', 'Unknown')})")