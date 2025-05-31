import os
import anthropic
import httpx

# Model-specific timeout configurations (in seconds)
MODEL_TIMEOUTS = {
    # Claude 4 series (potentially slower)
    "claude-4-opus": 240,
    "claude-4-sonnet": 180,
    # Claude 3.7 series  
    "claude-3-7-sonnet": 120,
    # Claude 3.5 series
    "claude-3-5-sonnet": 90,
    "claude-3-5-haiku": 60,
    # Claude 3 series
    "claude-3-opus": 180,
    "claude-3-sonnet": 90,
    "claude-3-haiku": 60,
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
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=default_timeout
)

def chat_completion(messages, model="claude-3-5-sonnet-20241022", temperature=0.0, max_tokens=None):
    """
    Send a sequence of chat messages to the Anthropic API and return the assistant's response text.
    Uses model-specific timeouts for better reliability with slower models.
    """
    # Get model-specific timeout
    timeout_seconds = get_timeout_for_model(model)
    model_timeout = httpx.Timeout(timeout_seconds)
    
    # Create client with model-specific timeout
    model_client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=model_timeout
    )
    
    params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    
    try:
        response = model_client.messages.create(**params)
        return response.content[0].text
    except Exception as e:
        # Log timeout information for debugging
        if "timeout" in str(e).lower():
            print(f"⏱️  Timeout after {timeout_seconds}s for model {model}: {e}")
        raise