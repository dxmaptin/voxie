"""
Supabase Client for Voxie - Agent Persistence
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env files if they exist
# Railway provides env vars directly, so this is optional
if os.path.exists('.env.local'):
    load_dotenv('.env.local', override=True)
    print("✅ Loaded environment from .env.local")
elif os.path.exists('.env'):
    load_dotenv('.env', override=True)
    print("✅ Loaded environment from .env")
else:
    print("✅ Using system environment variables (Railway/production)")

class SupabaseClient:
    def __init__(self):
        # Get environment variables (works both locally and on Railway)
        self.url = os.getenv("SUPABASE_URL", "").strip()
        self.key = os.getenv("SUPABASE_ANON_KEY", "").strip()

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")

        self.client: Client = create_client(self.url, self.key)
        print(f"✅ Supabase connected: {self.url}")

# Create singleton instance
supabase_client = SupabaseClient()
