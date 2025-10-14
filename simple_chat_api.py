#!/usr/bin/env python3
import sys
import json
import os
from agent import agent
from langchain_core.messages import HumanMessage

def main():
    if len(sys.argv) < 2:
        print("Error: No message provided", file=sys.stderr)
        sys.exit(1)
    
    user_message = sys.argv[1]
    
    try:
        # Use your existing agent for text conversations
        initial_state = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Run the agent
        result = agent.invoke(initial_state)
        
        # Extract the AI response (last message)
        messages = result["messages"]
        ai_response = None
        
        for msg in reversed(messages):
            if hasattr(msg, 'content') and not isinstance(msg, HumanMessage):
                ai_response = msg.content
                break
        
        if ai_response:
            # Add medical disclaimer if not already present
            if "not a doctor" not in ai_response.lower() and "disclaimer" not in ai_response.lower():
                ai_response += "\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only and should not replace professional medical advice. Please consult with your oncologist or healthcare provider for personalized medical guidance."
            
            print(ai_response)
        else:
            print("I'm sorry, I couldn't generate a response. Please try again.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error processing message: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()