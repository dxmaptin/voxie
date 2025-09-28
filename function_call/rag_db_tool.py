import json
import numpy as np
import os
from typing import Dict, Tuple, List, Union, Optional
from openai import OpenAI

# Try to import faiss, fall back to simple search if not available
try:
    import faiss
    FAISS_AVAILABLE = True
    # Type aliases for when faiss is available
    FaissIndex = faiss.Index
except ImportError:
    print("⚠️ FAISS not available, using simple text search fallback")
    FAISS_AVAILABLE = False
    # Type alias for when faiss is not available
    FaissIndex = None

# Load OpenAI API key from environment variable
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("⚠️ OPENAI_API_KEY environment variable is not set. Some features will be disabled.")
    client = None
else:
    try:
        # Initialize OpenAI client with API key
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize OpenAI client: {e}")
        client = None

# Load product database
with open('test_products.json', 'r') as f:
    PRODUCT_DATABASE = json.load(f)

def embed_text(text: str) -> np.ndarray:
    """Generate embedding vector using OpenAI embeddings API"""
    if client is None:
        # Return a dummy embedding if OpenAI client is not available
        print("⚠️ OpenAI client not available, returning dummy embedding")
        return np.zeros(1536, dtype=np.float32)  # Standard embedding size

    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"  # or another available embedding model
        )
        embedding = response.data[0].embedding
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        print(f"⚠️ Failed to generate embedding: {e}")
        return np.zeros(1536, dtype=np.float32)

def create_faiss_index() -> Tuple[Optional[FaissIndex], Dict[int, dict]]:
    """Create FAISS index for product search using OpenAI embeddings"""
    if not FAISS_AVAILABLE:
        print("⚠️ FAISS not available, returning None index")
        return None, {}
    
    print("Creating FAISS index with OpenAI embeddings...")
    
    embeddings = []
    id_to_product = {}
    
    for i, product in enumerate(PRODUCT_DATABASE):
        # Combine product text fields for embedding
        text = f"{product['name']} {product['category']} {product['description']} {' '.join(product.get('features', []))}"
        embedding = embed_text(text)
        embeddings.append(embedding)
        id_to_product[i] = product
    
    embeddings_array = np.array(embeddings).astype('float32')
    index = faiss.IndexFlatIP(embeddings_array.shape[1])  # Inner product index for similarity
    index.add(embeddings_array)
    
    print(f"✅ Created FAISS index with {len(embeddings)} products")
    return index, id_to_product

def simple_text_search(query: str, limit: int = 5) -> List[dict]:
    """Simple text-based search fallback when FAISS is not available"""
    query_lower = query.lower()
    results = []
    
    for product in PRODUCT_DATABASE:
        score = 0
        text = f"{product['name']} {product['category']} {product['description']} {' '.join(product.get('features', []))}".lower()
        
        # Simple keyword matching
        for word in query_lower.split():
            if word in text:
                score += 1
        
        if score > 0:
            results.append((score, product))
    
    # Sort by score and return top results
    results.sort(key=lambda x: x[0], reverse=True)
    return [product for score, product in results[:limit]]

def load_index_and_mapping():
    """Load or create FAISS index and id-to-product mapping"""
    try:
        return create_faiss_index()
    except Exception as e:
        print(f"Error creating index: {e}")
        return None, {}

# Create index when module is run directly
if __name__ == "__main__":
    index, mapping = create_faiss_index()
    print("FAISS index created successfully!")
