import os
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional

class SimpleAIClient:
    """
    Simple AI client that makes direct HTTP calls to avoid library conflicts
    """
    
    def __init__(self):
        # Check available providers
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        print(f"🔍 Available providers: OpenAI={'✅' if self.openai_key else '❌'}, Anthropic={'✅' if self.anthropic_key else '❌'}")
        
        if not self.openai_key and not self.anthropic_key:
            raise ValueError("Either OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable is required")
        
        # Default to anthropic if available, otherwise openai
        self.provider = os.getenv('AI_PROVIDER', 'anthropic' if self.anthropic_key else 'openai').lower()
        
        if self.provider == 'anthropic' and not self.anthropic_key:
            print("⚠️  Anthropic selected but no key found, switching to OpenAI")
            self.provider = 'openai'
        elif self.provider == 'openai' and not self.openai_key:
            print("⚠️  OpenAI selected but no key found, switching to Anthropic")
            self.provider = 'anthropic'
        
        self.model = self._get_model()
        print(f"✅ Using {self.provider} with {self.model}")
    
    def _get_model(self) -> str:
        """Get the model to use based on provider"""
        if self.provider == 'openai':
            return os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        else:
            return os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
    
    async def generate_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate AI response using direct HTTP calls"""
        
        try:
            if self.provider == 'openai':
                return await self._call_openai(prompt, conversation_history)
            else:
                return await self._call_anthropic(prompt, conversation_history)
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._get_fallback_response()
    
    async def _call_openai(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Make direct HTTP call to OpenAI API"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert system architect and specification designer helping users create comprehensive system specifications through natural conversation.

Your expertise includes:
- System analysis and architecture design
- Requirement gathering and specification writing
- Scenario-based development
- Performance and constraint analysis

Your personality:
- Friendly and encouraging
- Patient and thorough
- Able to adapt to different expertise levels
- Focused on practical, actionable guidance

Your goal is to guide users through discovering and defining their system requirements in a way that feels natural and collaborative."""
            }
        ]
        
        # Add recent conversation history
        if conversation_history:
            recent_history = conversation_history[-6:]  # Last 3 exchanges
            for exchange in recent_history:
                messages.append({
                    "role": exchange["role"],
                    "content": exchange["content"]
                })
        
        # Add current prompt
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    
    async def _call_anthropic(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """Make direct HTTP call to Anthropic API"""
        
        # Build conversation for Anthropic format
        conversation_text = ""
        if conversation_history:
            recent_history = conversation_history[-6:]
            for exchange in recent_history:
                role = "Human" if exchange["role"] == "user" else "Assistant"
                conversation_text += f"\n{role}: {exchange['content']}\n"
        
        full_prompt = f"""You are an expert system architect and specification designer helping users create comprehensive system specifications through natural conversation.

Your expertise includes:
- System analysis and architecture design
- Requirement gathering and specification writing
- Scenario-based development
- Performance and constraint analysis

Your personality:
- Friendly and encouraging
- Patient and thorough
- Able to adapt to different expertise levels
- Focused on practical, actionable guidance

Your goal is to guide users through discovering and defining their system requirements in a way that feels natural and collaborative.

{conversation_text}