#!/usr/bin/env python3
"""
AI client configuration and testing utility.
"""

import argparse
import os
import sys
from core.ai_client import chat_completion, list_available_models, get_current_config

def test_client(provider: str = None, model: str = None):
    """Test the AI client with a simple completion."""
    messages = [
        {"role": "user", "content": "Respond with exactly: 'AI client is working correctly'"}
    ]
    
    try:
        response = chat_completion(
            messages=messages,
            provider=provider,
            model=model,
            max_tokens=50
        )
        print(f"✅ Success: {response.strip()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_config():
    """Display current AI client configuration."""
    config = get_current_config()
    
    print("Current AI Client Configuration:")
    print(f"  Default Provider: {config['provider']}")
    print(f"  Default Model: {config['model']}")
    print()
    
    print("Environment Variables:")
    print(f"  AI_PROVIDER: {os.getenv('AI_PROVIDER', 'not set')}")
    print(f"  OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'not set')}")
    print(f"  ANTHROPIC_MODEL: {os.getenv('ANTHROPIC_MODEL', 'not set')}")
    print(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
    print(f"  ANTHROPIC_API_KEY: {'set' if os.getenv('ANTHROPIC_API_KEY') else 'not set'}")

def show_models():
    """Display available models for all providers."""
    models = list_available_models()
    
    print("Available Models:")
    for provider, model_list in models.items():
        print(f"\n{provider.upper()}:")
        for model in model_list:
            print(f"  - {model}")

def main():
    parser = argparse.ArgumentParser(description="AI client configuration and testing")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Show current configuration")
    
    # Models command
    models_parser = subparsers.add_parser("models", help="List available models")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test AI client connection")
    test_parser.add_argument("--provider", choices=["openai", "anthropic"], 
                            help="Provider to test")
    test_parser.add_argument("--model", help="Model to test")
    
    args = parser.parse_args()
    
    if args.command == "config":
        show_config()
    elif args.command == "models":
        show_models()
    elif args.command == "test":
        test_client(args.provider, args.model)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()