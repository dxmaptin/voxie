import os
import requests
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ragie configuration
RAGIE_API_KEY = "tnt_EamoMbhFb3G_3le04jIDwCRGTCkrw0hZCoYr6Bq1UtKb3jgBOLC276i"
RAGIE_DOCUMENT_ID = "f193f766-40fa-4b8b-ad50-49aa8b72da54"
RAGIE_BASE_URL = "https://api.ragie.ai"

class RagieKnowledgeBase:
    """Ragie knowledge base integration - works like the static JSON database"""

    def __init__(self):
        self.api_key = RAGIE_API_KEY
        self.document_id = RAGIE_DOCUMENT_ID
        self.base_url = RAGIE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def query_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query Ragie knowledge base - similar to how we search test_products.json
        Returns structured results that the voice agent can use
        """
        try:
            # Ragie retrieval endpoint
            url = f"{self.base_url}/retrievals"

            payload = {
                "query": query,
                "scope": {
                    "document_ids": [self.document_id]
                },
                "top_k": max_results
            }

            print(f"🔍 Querying Ragie with: {payload}")

            response = requests.post(url, headers=self.headers, json=payload)
            print(f"📡 Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Response error: {response.text}")
                return []

            response.raise_for_status()
            results = response.json()

            print(f"📄 Raw response: {json.dumps(results, indent=2)[:500]}...")

            # Transform Ragie results to match our product-like structure
            formatted_results = []
            chunks = results.get("scored_chunks", [])

            for item in chunks:
                formatted_result = {
                    "id": item.get("chunk", {}).get("id", "unknown"),
                    "content": item.get("chunk", {}).get("text", ""),
                    "metadata": item.get("chunk", {}).get("metadata", {}),
                    "score": item.get("score", 0.0),
                    "source": "ragie_knowledge_base"
                }
                formatted_results.append(formatted_result)

            return formatted_results

        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying Ragie: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []

    def get_document_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the uploaded document"""
        try:
            url = f"{self.base_url}/documents/{self.document_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error getting document info: {e}")
            return None

    def search_with_filters(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Advanced search with metadata filters
        Similar to how we filter products by price/category
        """
        try:
            url = f"{self.base_url}/retrievals"

            payload = {
                "query": query,
                "document_ids": [self.document_id],
                "top_k": max_results,
                "filters": filters or {},
                "include_summary": True
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            results = response.json()
            return [item for item in results.get("results", [])]

        except Exception as e:
            print(f"❌ Error in filtered search: {e}")
            return []

# Global instance - similar to how we load PRODUCT_DATABASE
ragie_kb = RagieKnowledgeBase()

def search_ragie_knowledge(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Main function to search Ragie knowledge base
    This replaces direct access to PRODUCT_DATABASE
    """
    return ragie_kb.query_knowledge(query, max_results)

def get_ragie_document_summary() -> Optional[str]:
    """Get summary of what's in the knowledge base"""
    doc_info = ragie_kb.get_document_info()
    if doc_info:
        return doc_info.get("summary", "Knowledge base document loaded")
    return None

# Test the connection
if __name__ == "__main__":
    print("🔍 Testing Ragie connection...")

    # Test document info
    doc_info = ragie_kb.get_document_info()
    if doc_info:
        print("✅ Document found:", doc_info.get("name", "Unknown"))

    # Test query
    test_results = search_ragie_knowledge("test query", 3)
    print(f"✅ Query test returned {len(test_results)} results")

    if test_results:
        print("Sample result:", test_results[0].get("content", "")[:100] + "...")