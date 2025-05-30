"""
Unified AI client interface supporting multiple providers (OpenAI, Anthropic).
Allows users to specify provider and model through configuration or parameters.
"""

import os
from typing import List, Dict, Any, Optional
from src.core import openai_client, anthropic_client

# Default models for each provider (latest as of 2025)
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-20241022"
}

# Available models by provider
AVAILABLE_MODELS = {
    "openai": [
        # Reasoning models o-series (2024-2025)
        "o4-mini",          # April 2025 - latest reasoning model
        "o3",               # April 2025 - advanced reasoning
        "o3-mini",          # January 2025 - efficient reasoning
        "o1",               # September 2024 - original reasoning
        "o1-preview",       # September 2024 - preview reasoning
        "o1-mini",          # September 2024 - lightweight reasoning
        # GPT-4.1 series (April 2025 - latest)
        "gpt-4.1",
        "gpt-4.1-mini", 
        "gpt-4.1-nano",
        # GPT-4o series (2024)
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-audio-preview",
        # GPT-4 Turbo
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        # Legacy models
        "gpt-4",
        "gpt-3.5-turbo"
    ],
    "anthropic": [
        # Claude 4 series (May 2025 - latest)
        "claude-4-opus",
        "claude-4-sonnet", 
        # Claude 3.7 series (February 2025)
        "claude-3-7-sonnet-20250224",
        # Claude 3.5 series (2024)
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        # Claude 3 series (March 2024)
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307"
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
        temperature: Sampling temperature (0.0 to 1.0). Note: o-series reasoning models may ignore this
        max_tokens: Maximum tokens in response. Note: o-series models use max_completion_tokens
        
    Returns:
        The assistant's response text
        
    Raises:
        ValueError: If provider is not supported or model is not available
        
    Note:
        OpenAI o-series reasoning models (o1, o3, o4-mini) use the same Chat Completions API
        but have special behavior: they ignore temperature and may require max_completion_tokens
        instead of max_tokens. They also perform internal reasoning steps before responding.
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