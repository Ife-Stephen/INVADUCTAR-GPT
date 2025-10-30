import os
import re
import shutil
from typing import List, Tuple
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTS_DIR = os.path.join(BASE_DIR, "texts")
PERSIST_DIR = os.path.join(BASE_DIR, "rag_store")

def extract_text_and_links(pdf_path: str) -> List[Tuple[str, List[str]]]:
    """Extract text and links from a PDF file."""
    reader = PdfReader(pdf_path)
    results = []
    for page in reader.pages:
        text = page.extract_text() or ""
        links = re.findall(r"https?://\S+", text)
        results.append((text, links))
    return results


def build_vectorstore(persist_dir: str = PERSIST_DIR) -> FAISS:
    """Rebuild the FAISS vector store from all PDFs in texts/."""
    print("🔍 Scanning PDF files...")

    if not os.path.exists(TEXTS_DIR):
        raise FileNotFoundError(f"❌ Folder not found: {TEXTS_DIR}")

    pdf_files = [f for f in os.listdir(TEXTS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise RuntimeError("⚠️ No PDF files found in the 'texts' directory.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )

    all_docs: List[Document] = []
    for fname in pdf_files:
        pdf_path = os.path.join(TEXTS_DIR, fname)
        print(f"📄 Processing {fname}...")
        pages = extract_text_and_links(pdf_path)

        for page_text, page_links in pages:
            chunks = splitter.split_text(page_text)
            for chunk in chunks:
                chunk_links = [url for url in page_links if url in chunk]
                all_docs.append(
                    Document(page_content=chunk, metadata={"source": fname, "links": chunk_links})
                )

    print(f"✅ Processed {len(all_docs)} text chunks in total.")

    # Rebuild FAISS index
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)

    print("⚙️ Generating embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vectordb = FAISS.from_documents(all_docs, embeddings)
    vectordb.save_local(persist_dir)

    print("🎉 Vector store rebuilt successfully!")
    return vectordb


if __name__ == "__main__":
    print("🔄 Starting RAG rebuild process...")
    try:
        build_vectorstore()
        print("✅ RAG index is ready for use.")
    except Exception as e:
        print(f"❌ Failed to rebuild RAG: {e}")
