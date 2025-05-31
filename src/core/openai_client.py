import os
from openai import OpenAI
import httpx

# Model-specific timeout configurations (in seconds)
MODEL_TIMEOUTS = {
    # Slower reasoning models need more time
    "gpt-4.1": 180,
    "gpt-4.1-mini": 120, 
    "gpt-4.1-nano": 90,
    "o1": 300,           # Reasoning models can be very slow
    "o1-preview": 300,
    "o1-mini": 180,
    "o3": 300,
    "o3-mini": 180,
    "o4-mini": 240,
    # Standard models
    "gpt-4o": 60,
    "gpt-4o-mini": 45,
    "gpt-4": 90,
    "gpt-4-turbo": 90,
    "gpt-3.5-turbo": 45,
}

def get_timeout_for_model(model: str) -> int:
    """Get appropriate timeout for a given model."""
    # Check exact match first
    if model in MODEL_TIMEOUTS:
        return MODEL_TIMEOUTS[model]
    
    # Check partial matches for model families
    for model_prefix, timeout in MODEL_TIMEOUTS.items():
        if model.startswith(model_prefix):
            return timeout
    
    # Default timeout for unknown models
    return 120

# Create client with default timeout
default_timeout = httpx.Timeout(120.0)  # 2 minutes default
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=default_timeout
)

def chat_completion(messages, model="gpt-4o", temperature=0.0, max_tokens=None):
    """
    Send a sequence of chat messages to the OpenAI API and return the assistant's response text.
    Uses model-specific timeouts for better reliability with slower models.
    """
    # Get model-specific timeout
    timeout_seconds = get_timeout_for_model(model)
    model_timeout = httpx.Timeout(timeout_seconds)
    
    # Create client with model-specific timeout
    model_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=model_timeout
    )
    
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
    
    try:
        response = model_client.chat.completions.create(**params)
        return response.choices[0].message.content
    except Exception as e:
        # Log timeout information for debugging
        if "timeout" in str(e).lower():
            print(f"⏱️  Timeout after {timeout_seconds}s for model {model}: {e}")
        raise
