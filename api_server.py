from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, base64, traceback
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import agent
from tools import analyze_image, explain_result
from supabase import create_client, Client
from openai import OpenAI

# -----------------------------
# 🔹 Initialize
# -----------------------------
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# 🔹 Conversation Persistence in Supabase
# -----------------------------
def load_conversation():
    try:
        res = supabase.table("conversations").select("messages").order("created_at", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
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
# 🔹 Helper: Clean AI Output
# -----------------------------
def extract_final_response(content: str) -> str:
    if not content:
        return ""
    lines = content.splitlines()
    filtered = [line.strip() for line in lines if not any(x in line.lower() for x in ["thought", "reasoning", "step", "analyz", "hmm"])]
    return "\n".join(filtered).strip() or content.strip()

# -----------------------------
# 🔹 Chat Route (Text only)
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

        return jsonify({
            "success": True,
            "response": ai_reply,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Chat failed: {e}"}), 500

# -----------------------------
# 🔹 Image Analysis (uploads to Supabase)
# -----------------------------
@app.route("/api/analyze-image", methods=["POST"])
def analyze_image_route():
    try:
        data = request.json or {}
        image_data = data.get("image")
        if not image_data or "," not in image_data:
            return jsonify({"success": False, "error": "Invalid or missing image data"}), 400

        image_bytes = base64.b64decode(image_data.split(",")[1])
        filename = f"mammogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = f"uploads/{filename}"

        # 🟢 Upload image to Supabase
        supabase.storage.from_("uploads").upload(file_path, image_bytes)
        public_url = supabase.storage.from_("uploads").get_public_url(file_path)

        command = f"ANALYZE_IMAGE: {public_url}"
        analysis = analyze_image.invoke(command)
        if not analysis or "error" in analysis:
            err = analysis.get("error", "Unknown error")
            print(f"❌ Analysis failed: {err}")
            return jsonify({"success": False, "error": f"Analysis failed: {err}"}), 500

        explanation = explain_result.invoke({"result": analysis})
        ai_response = explanation.get("result", "⚠️ No explanation generated.")

        conversation = load_conversation()
        conversation.append(HumanMessage(content=f"User uploaded image: {public_url}"))
        conversation.append(ToolMessage(content=str(analysis), tool_call_id="analyze_image"))
        conversation.append(AIMessage(content=ai_response))
        save_conversation(conversation)

        return jsonify({
            "success": True,
            "response": extract_final_response(ai_response),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "image_url": public_url
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"❌ Image analysis failed: {e}"}), 500

# -----------------------------
# 🔹 Embeddings (store & query via Supabase)
# -----------------------------
@app.route("/api/embed", methods=["POST"])
def embed_text():
    try:
        text = request.json.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "Text cannot be empty."}), 400

        vector = openai_client.embeddings.create(model="text-embedding-3-small", input=text).data[0].embedding
        supabase.table("embeddings").insert({
            "content": text,
            "vector": vector,
            "metadata": {"source": "api_upload"}
        }).execute()

        return jsonify({"success": True, "message": "Embedding stored successfully"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/search", methods=["POST"])
def semantic_search():
    try:
        query = request.json.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "Query cannot be empty."}), 400

        q_emb = openai_client.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
        res = supabase.rpc("match_embeddings", {"query_embedding": q_emb, "match_threshold": 0.7, "match_count": 5}).execute()

        return jsonify({"success": True, "results": res.data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# -----------------------------
# 🔹 Server
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
