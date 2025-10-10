# tools.py
import os
import json
from typing import Dict, Any, List, Tuple
from PIL import Image
import torch
from transformers import CLIPModel, CLIPProcessor
from openai import OpenAI
from dotenv import load_dotenv
from langchain_core.tools import tool


# For PDF + embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# --- Hugging Face router client via OpenAI-compatible wrapper ---
HF_BASE_URL = "https://router.huggingface.co/v1"
HF_MODEL = "deepseek-ai/DeepSeek-R1-0528:novita"
API_KEY = os.environ.get("TOKEN")

if not API_KEY:
    raise RuntimeError("⚠️ Please set TOKEN in your .env file.")

# ✅ Proper OpenAI-compatible client
client = OpenAI(api_key=API_KEY, base_url=HF_BASE_URL)

# --- CLIP model (vision) ---
CLIP_MODEL_ID = "openai/clip-vit-base-patch32"

_clip_device = "cuda" if torch.cuda.is_available() else "cpu"
_clip_model = CLIPModel.from_pretrained(CLIP_MODEL_ID).to(_clip_device)

# ✅ Do NOT set use_fast for CLIPProcessor (only applies to text tokenizers)
_clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)

# Load or build vectorstore
if os.path.exists("rag_store/index.faiss"):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    _vectordb = FAISS.load_local("rag_store", embeddings, allow_dangerous_deserialization=True)
else:
    from ingest_pdfs import build_vectorstore
    _vectordb = build_vectorstore()

_retriever = _vectordb.as_retriever(search_kwargs={"k": 5})

@tool
def analyze_image(image_path: str) -> Dict[str, Any]:
    """
    Analyze an image using a CLIP model.
    Returns: {"prediction": label, "confidence": float, "scores": {label: score}}
    """
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        return {"error": f"Unable to open image: {e}"}

    labels = ["normal tissue", "suspicious lesion", "malignant tumor", "artifact / poor quality"]

    inputs = _clip_processor(text=labels, images=image, return_tensors="pt", padding=True)
    for k, v in inputs.items():
        if isinstance(v, torch.Tensor):
            inputs[k] = v.to(_clip_device)

    with torch.no_grad():
        outputs = _clip_model(**inputs)

    logits = outputs.logits_per_image
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

    best_idx = int(probs.argmax())
    return {
        "prediction": labels[best_idx],
        "confidence": float(probs[best_idx]),
        "scores": {labels[i]: float(probs[i]) for i in range(len(labels))}
    }


def _call_hf_model(messages: List[Dict[str, str]], model: str = HF_MODEL) -> str:
    """Wrapper to safely call Hugging Face models via OpenAI API style."""
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=400,
    )
    try:
        return resp.choices[0].message.content
    except Exception:
        return str(resp)


@tool
def explain_result(result: Dict[str, Any]) -> Dict[str, str]:
    """
    Use DeepSeek LLM (Hugging Face) to convert the structured result into
    a human-friendly, medically cautious explanation.
    Returns: {"result": explanation}
    """
    system = {
        "role": "system",
        "content": (
            "You are a specialized medical assistant focused ONLY on breast cancer. Always include:\n"
            "1) Simple explanation of the image result.\n"
            "2) Disclaimer: you are not a doctor.\n"
            "3) Gentle, practical next steps.\n"
            "Keep it short (2–5 paragraphs max)."
        )
    }

    user = {
        "role": "user",
        "content": f"Image analysis result: {json.dumps(result)}\n\nExplain this in simple language."
    }

    resp = client.chat.completions.create(
        model=HF_MODEL,
        messages=[system, user],
        temperature=0.2,
        max_tokens=400,
    )

    try:
        content = resp.choices[0].message.content
    except Exception:
        content = str(resp)

    if "not a doctor" not in content.lower():
        content += "\n\n**Disclaimer:** I am not a medical professional. Please consult a qualified clinician."

    return {"result": content}   # ✅ dict output


@tool
def general_chat(user_text: str) -> Dict[str, str]:
    """
    Use DeepSeek to handle general text-based questions.
    Returns: {"result": reply}
    """
    system = {
        "role": "system",
        "content": (
            "You are a specialized medical assistant focused ONLY on breast cancer, with emphasis on Invasive Ductal Carcinoma (IDC). Answer general questions clearly and concisely. "
            "If medical, remind user to consult a doctor."
        )
    }
    user = {"role": "user", "content": user_text}

    resp = client.chat.completions.create(
        model=HF_MODEL,
        messages=[system, user],
        temperature=0.5,
        max_tokens=400,
    )

    try:
        content = resp.choices[0].message.content
    except Exception:
        content = str(resp)

    return {"result": content}   # ✅ standardized dict return

@tool
def rag_query(question: str) -> Dict[str, Any]:
    """
    Retrieve and generate an answer from ingested PDFs.
    Adds clickable inline citations like [1](https://...) and a reference section.
    """
    docs = _retriever.get_relevant_documents(question)

    if not docs:
        return {"result": "⚠️ No relevant documents found."}

    context_parts = []
    numbered_refs = []

    for i, doc in enumerate(docs, start=1):
        links = doc.metadata.get("links", [])
        if links:
            # Pick the first link for inline citation
            citation = f"[{i}]({links[0]})"
        else:
            citation = f"[{i}]"
        numbered_refs.append((i, links))
        context_parts.append(f"{doc.page_content.strip()} {citation}")

    context = "\n\n".join(context_parts)

    system = {
        "role": "system",
        "content": (
            "You are a retrieval-augmented assistant. Use the provided context to answer.\n"
            "Insert clickable inline citations like [1](https://...) exactly where evidence is used.\n"
            "At the end, include a References section with all sources."
        )
    }
    user = {
        "role": "user",
        "content": f"Question: {question}\n\nContext:\n{context}"
    }

    resp = client.chat.completions.create(
        model=HF_MODEL,
        messages=[system, user],
        temperature=0.2,
        max_tokens=500,
    )

    try:
        answer = resp.choices[0].message.content
    except Exception:
        answer = str(resp)

    # Build reference section with clickable links
    refs_text = "\n".join(
        f"[{i}]: {', '.join(f'[{link}]({link})' for link in links) if links else 'No link available'}"
        for i, links in numbered_refs
    )

    final_answer = f"{answer}\n\n---\n**References:**\n{refs_text}"

    return {"result": final_answer}