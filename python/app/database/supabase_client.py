import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # Load from .env automatically

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Create a single reusable Supabase client safely. If env vars are missing or initialization
# fails we keep `supabase` as None and provide helper functions callers can use.
supabase: Client | None = None

try:
	if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
		supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
	else:
		# keep supabase as None if env vars missing
		supabase = None
except Exception:
	# Initialization failed (network, invalid key, etc.) — leave supabase as None and let callers handle it
	supabase = None


def is_supabase_ready() -> bool:
	"""Return True if supabase client is initialized."""
	return supabase is not None