import os
from supabase import create_client, Client

_anon_client: Client | None = None
_admin_client: Client | None = None


def get_anon_client() -> Client:
    global _anon_client
    if _anon_client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_ANON_KEY", "")
        _anon_client = create_client(url, key)
    return _anon_client


def get_admin_client() -> Client:
    global _admin_client
    if _admin_client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        _admin_client = create_client(url, key)
    return _admin_client
