#!/usr/bin/env python3
import sys
import json
import os
from langchain_core.messages import HumanMessage, AIMessage
from agent import agent

def load_conversation():
    """Load existing conversation from JSON file"""
    data_file = "conversation.json"
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            messages = []
            for m in raw:
                if m["type"] == "human":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["type"] == "ai":
                    messages.append(AIMessage(content=m["content"]))
            return messages
        except Exception as e:
            print(f"Could not load saved conversation: {e}", file=sys.stderr)
    return []

def save_conversation(messages):
    """Save conversation to JSON file"""
    data_file = "conversation.json"
    serializable = []
    for m in messages:
        if isinstance(m, HumanMessage):
            serializable.append({"type": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            serializable.append({"type": "ai", "content": m.content})
    
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)

def extract_final_response(ai_message_content):
    """Extract only the final response, hiding agent thoughts"""
    # Split by common thought patterns and take the last meaningful part
    content = str(ai_message_content)
    
    # Remove thought patterns
    thought_markers = [
        "I need to",
        "Let me think",
        "I should",
        "Based on the",
        "Looking at",
        "I'll analyze",
        "First, I",
        "The user is asking"
    ]
    
    lines = content.split('\n')
    response_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not any(marker in line for marker in thought_markers):
            # Skip lines that look like internal reasoning
            if not (line.startswith('I need') or line.startswith('Let me') or 
                   line.startswith('I should') or line.startswith('Based on') or
                   line.startswith('Looking at') or line.startswith('I\'ll') or
                   line.startswith('First,')):
                response_lines.append(line)
    
    # If we have response lines, join them, otherwise return original
    if response_lines:
        return '\n'.join(response_lines)
    else:
        # Fallback: try to find the last substantial paragraph
        paragraphs = content.split('\n\n')
        for paragraph in reversed(paragraphs):
            if len(paragraph.strip()) > 50:  # Substantial content
                return paragraph.strip()
        return content

def main():
    if len(sys.argv) < 2:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)
    
    user_message = sys.argv[1]
    
    try:
        # Load existing conversation
        conversation = load_conversation()
        
        # Add user message
        conversation.append(HumanMessage(content=user_message))
        
        # Get AI response using your agent
        result = agent.invoke({"messages": conversation})
        conversation = result["messages"]
        
        # Save conversation
        save_conversation(conversation)
        
        # Get the latest AI message and extract clean response
        latest_ai_message = ""
        for msg in reversed(conversation):
            if isinstance(msg, AIMessage):
                latest_ai_message = extract_final_response(msg.content)
                break
        
        # Output the clean response
        print(latest_ai_message)
        
    except Exception as e:
        print(f"Error processing message: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()