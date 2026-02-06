import pytest
from backend.database import get_supabase_client

def test_supabase_connection():
    """Test that we can connect to Supabase"""
    client = get_supabase_client()
    assert client is not None
    # Try a simple query to verify connection
    result = client.table('recipes').select('count').execute()
    assert result is not None
