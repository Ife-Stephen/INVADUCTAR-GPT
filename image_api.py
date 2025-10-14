#!/usr/bin/env python3
import sys
import json
import os
from agent import agent
from langchain_core.messages import HumanMessage

def main():
    if len(sys.argv) < 2:
        print("Error: No image path provided", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        # Check if file exists and is a valid image
        if not os.path.exists(image_path):
            print("Error: Image file not found.", file=sys.stderr)
            sys.exit(1)
        
        # Get file extension to determine image type
        file_ext = os.path.splitext(image_path)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.dcm', '.dicom', '.tiff', '.bmp']
        
        if file_ext not in valid_extensions:
            print("Error: Unsupported image format. Please upload JPG, PNG, DICOM, or TIFF files.", file=sys.stderr)
            sys.exit(1)
        
        # Use your existing agent with the ANALYZE_IMAGE command
        initial_state = {
            "messages": [HumanMessage(content=f"ANALYZE_IMAGE: {image_path}")]
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
            print(ai_response)
        else:
            print("Error: No response generated from image analysis", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error analyzing mammogram: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()