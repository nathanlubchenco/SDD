"""
Unified AI client interface supporting multiple providers (OpenAI, Anthropic).
Allows users to specify provider and model through configuration or parameters.
"""

import os
from typing import List, Dict, Any, Optional
from core import openai_client, anthropic_client

# Default models for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-sonnet-20240229"
}

# Available models by provider
AVAILABLE_MODELS = {
    "openai": [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ],
    "anthropic": [
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229"
    ]
}

def get_default_provider() -> str:
    """Get the default provider from environment or fallback to OpenAI."""
    return os.getenv("AI_PROVIDER", "openai").lower()

def get_default_model(provider: Optional[str] = None) -> str:
    """Get the default model for a provider."""
    if provider is None:
        provider = get_default_provider()
    
    # Check for provider-specific environment variable
    env_var = f"{provider.upper()}_MODEL"
    env_model = os.getenv(env_var)
    if env_model:
        return env_model
    
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["openai"])

def chat_completion(
    messages: List[Dict[str, str]], 
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None
) -> str:
    """
    Send messages to the specified AI provider and return the response.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        provider: AI provider ('openai' or 'anthropic'). Defaults to env AI_PROVIDER or 'openai'
        model: Model name. Defaults to provider default or env {PROVIDER}_MODEL
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        
    Returns:
        The assistant's response text
        
    Raises:
        ValueError: If provider is not supported or model is not available
    """
    if provider is None:
        provider = get_default_provider()
    
    if model is None:
        model = get_default_model(provider)
    
    provider = provider.lower()
    
    # Validate provider
    if provider not in ["openai", "anthropic"]:
        raise ValueError(f"Unsupported provider: {provider}. Must be 'openai' or 'anthropic'")
    
    # Validate model for provider
    if provider in AVAILABLE_MODELS and model not in AVAILABLE_MODELS[provider]:
        available = ", ".join(AVAILABLE_MODELS[provider])
        raise ValueError(f"Model '{model}' not available for {provider}. Available: {available}")
    
    # Route to appropriate client
    if provider == "openai":
        return openai_client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "anthropic":
        return anthropic_client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

def list_available_models(provider: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List available models for all providers or a specific provider.
    
    Args:
        provider: Specific provider to list models for, or None for all
        
    Returns:
        Dict mapping provider names to lists of available models
    """
    if provider is None:
        return AVAILABLE_MODELS.copy()
    
    provider = provider.lower()
    if provider in AVAILABLE_MODELS:
        return {provider: AVAILABLE_MODELS[provider]}
    else:
        raise ValueError(f"Unknown provider: {provider}")

def get_current_config() -> Dict[str, Any]:
    """Get current AI client configuration."""
    provider = get_default_provider()
    model = get_default_model(provider)
    
    return {
        "provider": provider,
        "model": model,
        "available_providers": list(AVAILABLE_MODELS.keys()),
        "available_models": AVAILABLE_MODELS
    }