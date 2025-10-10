import os
import re
from typing import List, Tuple
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader

TEXTS_DIR = "texts"

def extract_text_and_links(pdf_path: str) -> List[Tuple[str, List[str]]]:
    """
    Extract text and links from a PDF file.
    Returns a list of (page_text, [links]) tuples.
    """
    reader = PdfReader(pdf_path)
    results = []

    for page in reader.pages:
        text = page.extract_text() or ""
        # Find hyperlinks
        links = re.findall(r"https?://\S+", text)
        results.append((text, links))

    return results


def build_vectorstore(persist_dir: str = "rag_store") -> FAISS:
    """
    Ingest all PDFs in `texts/`, split into chunks, and store in FAISS.
    Each chunk has metadata with its own links.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )

    all_docs: List[Document] = []

    for fname in os.listdir(TEXTS_DIR):
        if not fname.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(TEXTS_DIR, fname)
        pages = extract_text_and_links(pdf_path)

        for page_text, page_links in pages:
            chunks = splitter.split_text(page_text)
            for chunk in chunks:
                # Only keep links present in this chunk
                chunk_links = [url for url in page_links if url in chunk]
                all_docs.append(
                    Document(page_content=chunk, metadata={"source": fname, "links": chunk_links})
                )

    if not all_docs:
        raise RuntimeError("⚠️ No PDF documents found to ingest.")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.from_documents(all_docs, embeddings)

    vectordb.save_local(persist_dir)
    return vectordb
