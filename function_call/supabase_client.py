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
            # Print diagnostic info
            print(f"❌ SUPABASE_URL: {'SET' if self.url else 'NOT SET'}")
            print(f"❌ SUPABASE_ANON_KEY: {'SET (length: {len(self.key) if self.key else 0})' if self.key else 'NOT SET'}")
            print(f"❌ Available env vars: {sorted([k for k in os.environ.keys() if 'SUPABASE' in k or 'LIVEKIT' in k])}")
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")

        # Debug: Check for whitespace/newlines
        print(f"🔍 URL has whitespace: {self.url != self.url.strip()}")
        print(f"🔍 Key has whitespace: {self.key != self.key.strip()}")
        print(f"🔍 Key length after strip: {len(self.key)}")

        try:
            self.client: Client = create_client(self.url, self.key)
            print(f"✅ Supabase connected: {self.url}")
        except Exception as e:
            print(f"❌ Failed to create Supabase client: {str(e)}")
            print(f"   URL: {self.url}")
            print(f"   Key length: {len(self.key) if self.key else 0}")
            print(f"   Key first 20 chars: {self.key[:20] if self.key else 'N/A'}")
            print(f"   Key last 20 chars: {self.key[-20:] if self.key else 'N/A'}")
            raise

# Create singleton instance
supabase_client = SupabaseClient()
