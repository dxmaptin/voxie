"""
Supabase Client for Voxie - Agent Persistence
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables with fallback for Railway
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
    print("✅ Supabase client loaded .env.local", flush=True)
elif os.path.exists(".env"):
    load_dotenv(".env")
    print("✅ Supabase client loaded .env", flush=True)
else:
    print("⚠️ Supabase client using system environment variables (Railway/production)", flush=True)

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

        self.client: Client = create_client(self.url, self.key)
        print(f"✅ Supabase connected: {self.url}")

supabase_client = SupabaseClient()
