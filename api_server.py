from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent import agent
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

DATA_FILE = "conversation.json"

def load_conversation():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            messages = []
            for m in raw:
                if m["type"] == "human":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["type"] == "ai":
                    messages.append(AIMessage(content=m["content"]))
                elif m["type"] == "tool":
                    messages.append(ToolMessage(content=m["content"], tool_call_id=m.get("tool_call_id", "")))
                else:
                    messages.append(AIMessage(content=m["content"]))
            return messages
        except Exception as e:
            print(f"Could not load saved conversation: {e}")
    return []

def save_conversation(messages):
    serializable = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serializable.append({"type": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serializable.append({"type": "ai", "content": m.content})
        elif isinstance(m, ToolMessage):
            serializable.append({"type": "tool", "content": m.content, "tool_call_id": getattr(m, "tool_call_id", "")})
        else:
            serializable.append({"type": "unknown", "content": str(m)})
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Load existing conversation
        conversation = load_conversation()
        
        # Add user message
        conversation.append(HumanMessage(content=user_message))
        
        # Get AI response using your agent
        result = agent.invoke({"messages": conversation})
        conversation = result["messages"]
        
        # Save conversation
        save_conversation(conversation)
        
        # Get the latest AI message
        latest_ai_message = ""
        for msg in reversed(conversation):
            if isinstance(msg, AIMessage):
                latest_ai_message = msg.content
                break
        
        return jsonify({
            "success": True,
            "response": latest_ai_message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    try:
        data = request.json
        image_data = data.get('image', '')  # base64 encoded image
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        # Load existing conversation
        conversation = load_conversation()
        
        # Add image analysis command
        cmd = f"ANALYZE_IMAGE: {tmp_path}"
        conversation.append(HumanMessage(content=cmd))
        
        # Get AI response using your agent
        result = agent.invoke({"messages": conversation})
        conversation = result["messages"]
        
        # Save conversation
        save_conversation(conversation)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Get the latest AI message
        latest_ai_message = ""
        for msg in reversed(conversation):
            if isinstance(msg, AIMessage):
                latest_ai_message = msg.content
                break
        
        return jsonify({
            "success": True,
            "response": latest_ai_message
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    try:
        conversation = load_conversation()
        messages = []
        
        for msg in conversation:
            if isinstance(msg, HumanMessage):
                messages.append({
                    "type": "user",
                    "content": msg.content,
                    "timestamp": "2024-01-01T00:00:00Z"  # You might want to add real timestamps
                })
            elif isinstance(msg, AIMessage):
                messages.append({
                    "type": "ai",
                    "content": msg.content,
                    "timestamp": "2024-01-01T00:00:00Z"
                })
        
        return jsonify({
            "success": True,
            "messages": messages
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    try:
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        
        return jsonify({
            "success": True,
            "message": "Conversation cleared"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)