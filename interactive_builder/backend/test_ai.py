#!/usr/bin/env python3
"""
Simple test script for the AI client
"""

import asyncio
import os
from simple_ai_client_complete import SimpleAIClient as AIClient

async def test_ai_client():
    """Test the AI client functionality"""
    
    print("🧪 Testing AI Client...")
    
    # Check environment
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
    
    if not openai_key and not anthropic_key:
        print("❌ No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        return False
    
    try:
        # Initialize client
        print("\n🔧 Initializing AI client...")
        client = AIClient()
        
        # Test simple response
        print("💬 Testing simple response...")
        response = await client.generate_response(
            "Please respond with exactly: 'AI client test successful'"
        )
        
        print(f"   Response: {response}")
        
        if "successful" in response.lower():
            print("✅ AI client test passed!")
            return True
        else:
            print("⚠️  AI client responded but message unexpected")
            return False
            
    except Exception as e:
        print(f"❌ AI client test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_client())
    exit(0 if success else 1)