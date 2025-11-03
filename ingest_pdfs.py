import os
import re
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
from supabase import create_client

# -----------------------------
# 🔹 Supabase Setup
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("❌ Supabase credentials missing. Please set SUPABASE_URL and SUPABASE_KEY.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# 🔹 Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTS_DIR = os.path.join(BASE_DIR, "texts")


def extract_text_and_links(pdf_path: str) -> List[Tuple[str, List[str]]]:
    """Extract text and links from a PDF file."""
    reader = PdfReader(pdf_path)
    results = []
    for page in reader.pages:
        text = page.extract_text() or ""
        links = re.findall(r"https?://\S+", text)
        results.append((text, links))
    return results


def build_vectorstore():
    """Extract text, generate embeddings, and upload to Supabase."""
    print("🔍 Scanning PDF files...")

    if not os.path.exists(TEXTS_DIR):
        raise FileNotFoundError(f"❌ Folder not found: {TEXTS_DIR}")

    pdf_files = [f for f in os.listdir(TEXTS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise RuntimeError("⚠️ No PDF files found in the 'texts' directory.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_chunks = 0
    for fname in pdf_files:
        pdf_path = os.path.join(TEXTS_DIR, fname)
        print(f"📄 Processing {fname}...")
        pages = extract_text_and_links(pdf_path)

        for page_text, page_links in pages:
            chunks = splitter.split_text(page_text)
            for chunk in chunks:
                chunk_links = [url for url in page_links if url in chunk]
                metadata = {"source": fname, "links": chunk_links}

                # Generate embedding
                embedding = embedder.embed_query(chunk)

                # Insert into Supabase
                try:
                    supabase.table("embeddings").insert({
                        "content": chunk,
                        "metadata": metadata,
                        "embedding": embedding
                    }).execute()
                    total_chunks += 1
                except Exception as e:
                    print(f"⚠️ Failed to insert chunk: {e}")

    print(f"🎉 Successfully uploaded {total_chunks} chunks to Supabase `embeddings` table.")
    print("✅ RAG index is now stored in the cloud (pgvector).")


if __name__ == "__main__":
    print("🔄 Starting RAG ingestion...")
    try:
        build_vectorstore()
        print("✅ All done!")
    except Exception as e:
        print(f"❌ Failed to build RAG index: {e}")


