import os
import re
import base64
import traceback
import json
from datetime import datetime
from typing import List, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
# from langchain_community.embeddings import HuggingFaceEmbeddings
from supabase import create_client, Client
from agent import agent
from tools import analyze_image, explain_result
# from pypdf import PdfReader

# -----------------------------
# 🔹 Flask App Setup
# -----------------------------
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# -----------------------------
# 🔹 Environment Config
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# 🔹 Conversation Persistence
# -----------------------------
def load_conversation():
    try:
        res = supabase.table("conversations").select("messages").order("created_at", desc=True).limit(1).execute()
        if res.data:
            raw = res.data[0]["messages"]
            messages = []
            for m in raw:
                t = m.get("type", "")
                if t == "human":
                    messages.append(HumanMessage(content=m["content"]))
                elif t == "ai":
                    messages.append(AIMessage(content=m["content"]))
                elif t == "tool":
                    messages.append(ToolMessage(content=m["content"], tool_call_id=m.get("tool_call_id", "")))
            return messages
    except Exception as e:
        print(f"⚠️ Failed to load conversation: {e}")
    return []

def save_conversation(messages):
    try:
        serializable = []
        for m in messages:
            if isinstance(m, HumanMessage):
                serializable.append({"type": "human", "content": m.content})
            elif isinstance(m, AIMessage):
                serializable.append({"type": "ai", "content": m.content})
            elif isinstance(m, ToolMessage):
                serializable.append({"type": "tool", "content": m.content})
        supabase.table("conversations").insert({"messages": serializable}).execute()
    except Exception as e:
        print(f"⚠️ Failed to save conversation: {e}")

# -----------------------------
# 🔹 Clean AI Output
# -----------------------------
def extract_final_response(content: str) -> str:
    if not content:
        return ""
    lines = content.splitlines()
    filtered = [
        line.strip() for line in lines
        if not any(x in line.lower() for x in ["thought", "reasoning", "step", "hmm"])
    ]
    return "\n".join(filtered).strip() or content.strip()

# -----------------------------
# 🔹 Chat Route
# -----------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"success": False, "error": "Message cannot be empty."}), 400

        conversation = load_conversation()
        conversation.append(HumanMessage(content=user_message))

        result = agent.invoke({"messages": conversation})
        conversation = result["messages"]
        save_conversation(conversation)

        ai_reply = next(
            (extract_final_response(m.content) for m in reversed(conversation) if isinstance(m, AIMessage)),
            "⚠️ No response generated."
        )
        return jsonify({"success": True, "response": ai_reply, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# -----------------------------
# 🔹 Image Analysis
# -----------------------------
@app.route("/api/analyze-image", methods=["POST"])
def analyze_image_route():
    try:
        data = request.json or {}
        image_data = data.get("image")
        if not image_data or "," not in image_data:
            return jsonify({"success": False, "error": "Invalid image data"}), 400

        image_bytes = base64.b64decode(image_data.split(",")[1])
        filename = f"mammogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        remote_path = f"uploads/{filename}"

        supabase.storage.from_("uploads").upload(remote_path, image_bytes)
        image_url = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{filename}"

        command = f"ANALYZE_IMAGE: {image_url}"
        analysis = analyze_image.invoke(command)
        explanation = explain_result.invoke({"result": analysis})
        ai_response = explanation.get("result", "⚠️ No explanation generated.")

        conversation = load_conversation()
        conversation.append(HumanMessage(content=f"User uploaded image: {image_url}"))
        conversation.append(ToolMessage(content=str(analysis), tool_call_id="analyze_image"))
        conversation.append(AIMessage(content=ai_response))
        save_conversation(conversation)

        return jsonify({
            "success": True,
            "response": extract_final_response(ai_response),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "image_url": image_url
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Image analysis failed: {e}"}), 500

# -----------------------------
# 🔹 Embeddings API (Hugging Face + Supabase)
# -----------------------------
@app.route("/api/embed", methods=["POST"])
def embed_text():
    try:
        text = request.json.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "Text cannot be empty."}), 400

        embedding = embedder.embed_query(text)
        supabase.table("embeddings").insert({
            "content": text,
            "metadata": {"source": "api_upload"},
            "embedding": embedding
        }).execute()
        return jsonify({"success": True, "message": "Embedding stored successfully"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# -----------------------------
# 🔹 Semantic Search
# -----------------------------
@app.route("/api/search", methods=["POST"])
def semantic_search():
    try:
        query = request.json.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "Query cannot be empty."}), 400

        query_embedding = embedder.embed_query(query)

        res = supabase.rpc("match_embeddings", {
            "query_embedding": query_embedding,
            "match_threshold": 0.7,
            "match_count": 5
        }).execute()

        return jsonify({"success": True, "results": res.data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# -----------------------------
# 🔹 Server Start
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
