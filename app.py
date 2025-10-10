import os
import json
import tempfile
import streamlit as st
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from agent import agent

# ---------------------------
# Config
# ---------------------------
st.set_page_config(page_title="INVADUCTAR GPT", layout="centered")
st.title("🩺 INVADUCTAR GPT")

DATA_FILE = "conversation.json"

# ---------------------------
# Helpers
# ---------------------------
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
            st.warning(f"Could not load saved conversation: {e}")
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

def clear_conversation():
    st.session_state["conversation"] = []
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# ---------------------------
# State initialization
# ---------------------------
if "conversation" not in st.session_state:
    st.session_state["conversation"] = load_conversation()

# ---------------------------
# UI
# ---------------------------
st.markdown(
    "Upload a mammogram image and click **Analyze** to see a structured result "
    "and a human-friendly explanation."
)

uploaded = st.file_uploader("Upload a medical image (jpg, png)", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns([1, 3])

with col1:
    if uploaded:
        st.image(uploaded, caption="Uploaded image", use_container_width=True)

    if st.button("Load Demo Image (sample)"):
        st.warning("Please upload a demo image file (not provided).")

    # --- Clear Conversation Button ---
    if st.button("Clear Conversation"):
        clear_conversation()
        st.success("✅ Conversation cleared successfully!")  # Toast message
        st.rerun()


with col2:
    st.subheader("Conversation")
    for m in st.session_state["conversation"]:
        if isinstance(m, HumanMessage):
            st.chat_message("user").write(m.content)
        elif isinstance(m, ToolMessage):
            st.chat_message("assistant").write(f"🔧 Tool [{m.tool_call_id}]: {m.content}")
        elif isinstance(m, AIMessage):
            st.chat_message("assistant").write(m.content)
        else:
            st.chat_message("assistant").write(str(m))

# ---------------------------
# Handle Image Analysis
# ---------------------------
if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    if st.button("Analyze Image"):
        cmd = f"ANALYZE_IMAGE: {tmp_path}"
        st.session_state["conversation"].append(HumanMessage(content=cmd))
        try:
            result = agent.invoke({"messages": st.session_state["conversation"]})
            st.session_state["conversation"] = result["messages"]
            # --- Save conversation persistently ---
            save_conversation(st.session_state["conversation"])
            st.success("✅ Conversation saved!")  # Toast message
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Agent error: {e}")

# ---------------------------
# General Chat
# ---------------------------
if user_text := st.chat_input("Ask a question (general):"):
    st.session_state["conversation"].append(HumanMessage(content=user_text.strip()))
    try:
        result = agent.invoke({"messages": st.session_state["conversation"]})
        st.session_state["conversation"] = result["messages"]
        save_conversation(st.session_state["conversation"])
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Agent error: {e}")

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown(
    "**Disclaimer:** This demo is for informational purposes only. "
    "It is not a medical diagnosis. Always consult a qualified healthcare professional."
)
