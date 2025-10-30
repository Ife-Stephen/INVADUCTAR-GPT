from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import base64
import traceback
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import agent
from tools import analyze_image, explain_result
from datetime import datetime

app = Flask(__name__)
# Allow all origins for development
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATA_FILE = "conversation.json"


# -----------------------------
# 🔹 Conversation Persistence
# -----------------------------
def load_conversation():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
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
    serializable = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serializable.append({"type": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serializable.append({"type": "ai", "content": m.content})
        elif isinstance(m, ToolMessage):
            serializable.append({"type": "tool", "content": m.content})
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)


# -----------------------------
# 🔹 Helper: Clean AI Output
# -----------------------------
def extract_final_response(content: str) -> str:
    """Remove thought-process text and return a clean assistant response."""
    if not content:
        return ""
    lines = content.splitlines()
    filtered = []
    for line in lines:
        if not any(x in line.lower() for x in ["thought", "reasoning", "step", "analyz", "hmm"]):
            filtered.append(line.strip())
    result = "\n".join(filtered).strip()
    return result or content.strip()


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
        return jsonify({"success": False, "error": f"Chat processing failed: {e}"}), 500


# -----------------------------
# 🔹 Image Analysis Route
# -----------------------------
@app.route("/api/analyze-image", methods=["POST"])
def analyze_image_route():
    try:
        data = request.json or {}
        image_data = data.get("image")
        if not image_data or "," not in image_data:
            return jsonify({"success": False, "error": "Invalid or missing image data"}), 400

        # Decode and save the uploaded image
        image_bytes = base64.b64decode(image_data.split(",")[1])
        tmp_dir = "uploads"
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = os.path.join(
            tmp_dir, f"mammogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        with open(tmp_path, "wb") as f:
            f.write(image_bytes)

        print(f"📸 Image saved to {tmp_path}")

        # Build the command string the agent expects
        command = f"ANALYZE_IMAGE: {tmp_path}"

        # Call the agent
        analysis = analyze_image.invoke(command)
        if not analysis or "error" in analysis:
            err = analysis.get("error", "Unknown error")
            print(f"❌ Analysis failed: {err}")
            return jsonify({"success": False, "error": f"Image analysis failed: {err}"}), 500

        # Optional explanation step
        explanation = explain_result.invoke({"result": analysis})
        ai_response = explanation.get("result", "⚠️ No detailed explanation generated.")

        # Update conversation memory
        conversation = load_conversation()
        conversation.append(HumanMessage(content=f"User uploaded image for analysis: {tmp_path}"))
        conversation.append(ToolMessage(content=str(analysis), tool_call_id="analyze_image"))
        conversation.append(AIMessage(content=ai_response))
        save_conversation(conversation)

        return jsonify({
            "success": True,
            "response": extract_final_response(ai_response),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "image_path": tmp_path
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": f"❌ Image analysis failed: {e}"}), 500


# -----------------------------
# 🔹 Conversation Routes
# -----------------------------
@app.route("/api/conversation", methods=["GET"])
def get_conversation():
    try:
        conversation = load_conversation()
        messages = []
        for msg in conversation:
            if isinstance(msg, HumanMessage):
                messages.append({"type": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"type": "ai", "content": extract_final_response(msg.content)})
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/clear-conversation", methods=["POST"])
def clear_conversation():
    try:
        # Delete conversation file
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        
        # Delete all uploaded images
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"⚠️ Failed to delete {file_path}: {e}")
        
        print("✅ All user data cleared successfully")
        return jsonify({"success": True, "message": "All conversation data and uploaded images have been permanently deleted."})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------
# 🔹 Server Start
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT env var
    print(f"🚀 Starting Flask server on http://0.0.0.0:{port}")
    print("✅ CORS enabled for all origins")

    app.run(host="0.0.0.0", port=port)

