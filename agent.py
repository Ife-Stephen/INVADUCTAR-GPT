# agent.py
import os
from typing import Annotated, Sequence, TypedDict, List
from dotenv import load_dotenv

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from tools import analyze_image, explain_result, general_chat
from langchain.memory import ConversationBufferMemory

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    return_messages=True
)



SYSTEM_PROMPT = SystemMessage(content=(
    "You are a specialized medical assistant focused ONLY on breast cancer, "
    "with emphasis on Invasive Ductal Carcinoma (IDC). "
    "You must:\n"
    "1. Answer ONLY if the question is related to breast cancer or IDC.\n"
    "2. Use the PDF knowledge base (via retrieval) and include inline Markdown citations with links ([1](https://...)).\n"
    "3. If the user asks about something outside breast cancer, reply politely: "
    "'I can only answer questions about breast cancer and invasive ductal carcinoma.'\n"
    "4. Always include a disclaimer: 'I am not a doctor. Please consult a qualified clinician.'\n"
    "5. Maintain context across the conversation and respond conversationally."
))


def process_node(state: AgentState) -> AgentState:
    """
    Process the incoming state messages. If the latest human message starts with ANALYZE_IMAGE: <path>,
    run the analyze_image tool, then explain_result, and append ToolMessage + AIMessage to state.
    Otherwise, call general_chat for free-text replies.
    """

    messages: List[BaseMessage] = list(state["messages"])

    # Find last human message
    last_human = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_human = m
            break

    # If there is a special ANALYZE_IMAGE command
    if last_human and last_human.content.strip().upper().startswith("ANALYZE_IMAGE:"):
        try:
            # parse path
            _, path = last_human.content.split(":", 1)
            image_path = path.strip()

            # ✅ Run vision tool with invoke()
            analysis = analyze_image.invoke(image_path)

            # Append ToolMessage
            tool_msg = ToolMessage(content=str(analysis), tool_call_id="analyze_image")
            messages.append(tool_msg)

            # Run explanation tool (DeepSeek) — now expects {"result": analysis}
            explanation = explain_result.invoke({"result": analysis})
            messages.append(AIMessage(content=explanation["result"]))
            return {"messages": messages}

        except Exception as e:
            err = f"Error during image analysis: {e}"
            messages.append(AIMessage(content=err))
            return {"messages": messages}


    # ✅ Default fallback: use general_chat for free-text replies
    try:
        reply = general_chat.invoke({"user_text": last_human.content if last_human else ""})
        messages.append(AIMessage(content=reply["result"]))
    except Exception as e:
        messages.append(AIMessage(content=f"Error generating reply: {e}"))

    return {"messages": messages}


# Build and compile the graph
graph = StateGraph(AgentState)
graph.add_node("process", process_node)
graph.add_edge(START, "process")
graph.add_edge("process", END)
agent = graph.compile()
