import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_completion(messages, model="gpt-4o", temperature=0.0, max_tokens=None):
    """
    Send a sequence of chat messages to the OpenAI API and return the assistant's response text.
    """
    params = {
        "model": model,
        "messages": messages,
    }
    
    # Handle o3 model parameter restrictions
    if model and "o3" in model:
        # o3 model only supports default temperature (1) and no max_tokens
        params["temperature"] = 1
    else:
        # Use provided temperature for other models
        params["temperature"] = temperature
        
        # Set max_tokens for non-o3 models
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
    response = client.chat.completions.create(**params)
    return response.choices[0].message.content
