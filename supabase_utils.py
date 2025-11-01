import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "rag-data"

def upload_file(local_path: str, remote_path: str):
    """Upload a local file to Supabase Storage."""
    with open(local_path, "rb") as f:
        res = supabase.storage.from_(BUCKET_NAME).upload(remote_path, f)
    print(f"📤 Uploaded {remote_path} to Supabase.")
    return res

def download_file(remote_path: str, local_path: str):
    """Download a file from Supabase Storage."""
    res = supabase.storage.from_(BUCKET_NAME).download(remote_path)
    with open(local_path, "wb") as f:
        f.write(res)
    print(f"📥 Downloaded {remote_path} to {local_path}")
