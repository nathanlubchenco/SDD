import os
import sys
import asyncio
from typing import List, Dict, Any, Optional

# For now, use independent AI client to avoid version conflicts
# TODO: Re-enable SDD integration once version conflicts are resolved
USE_SDD_CLIENT = False
print("🔧 Using independent AI client (avoiding version conflicts)")

import openai
from anthropic import Anthropic

class AIClient:
    """
    AI client that uses the same configuration as the main SDD project
    """
    
    def __init__(self):
        # Check available providers
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        print(f"🔍 Available providers: OpenAI={'✅' if openai_key else '❌'}, Anthropic={'✅' if anthropic_key else '❌'}")
        
        # Use environment variables (same as main SDD project expects)
        # Default to anthropic to avoid OpenAI proxy conflicts
        self.provider = os.getenv('AI_PROVIDER', 'anthropic' if anthropic_key else 'openai').lower()
        
        if self.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            try:
                # Try basic initialization first
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
                print(f"✅ OpenAI client initialized with {self.model}")
            except TypeError as e:
                if 'proxies' in str(e):
                    print(f"⚠️  OpenAI client proxy issue, trying alternative initialization...")
                    # Try with minimal parameters to avoid proxy conflicts
                    try:
                        import openai._client
                        self.openai_client = openai._client.AsyncOpenAI(api_key=api_key)
                        self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
                        print(f"✅ OpenAI client initialized (alternative method) with {self.model}")
                    except Exception as e2:
                        print(f"❌ Alternative OpenAI initialization failed: {e2}")
                        raise ValueError(f"Cannot initialize OpenAI client. Try setting AI_PROVIDER=anthropic")
                else:
                    print(f"❌ Failed to initialize OpenAI client: {e}")
                    raise
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                raise
            
        elif self.provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            
            try:
                self.anthropic_client = Anthropic(api_key=api_key)
                self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
                print(f"✅ Anthropic client initialized with {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Anthropic client: {e}")
                raise
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}. Use 'openai' or 'anthropic'")
    
    async def generate_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate AI response using the configured provider
        """
        try:
            if self.provider == 'openai':
                return await self._generate_openai_response(prompt, conversation_history)
            elif self.provider == 'anthropic':
                return await self._generate_anthropic_response(prompt, conversation_history)
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return self._get_fallback_response()
    
    async def _generate_openai_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate response using OpenAI API"""
        
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
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        # Add recent conversation history for context
        if conversation_history:
            # Include last few exchanges for context (limit to avoid token overflow)
            recent_history = conversation_history[-6:]  # Last 3 exchanges
            for i, exchange in enumerate(recent_history):
                if i < len(messages) - 1:  # Insert before the current prompt
                    messages.insert(-1, {
                        "role": exchange["role"],
                        "content": exchange["content"]
                    })
        
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_anthropic_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate response using Anthropic API"""
        
        # Anthropic uses a different message format
        system_prompt = """You are an expert system architect and specification designer helping users create comprehensive system specifications through natural conversation.

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

        # Build conversation for Anthropic format
        conversation_text = ""
        if conversation_history:
            recent_history = conversation_history[-6:]
            for exchange in recent_history:
                role = "Human" if exchange["role"] == "user" else "Assistant"
                conversation_text += f"\n{role}: {exchange['content']}\n"
        
        full_prompt = f"{system_prompt}\n\nConversation context:{conversation_text}\n\nHuman: {prompt}\n\nAssistant:"
        
        # Note: Using synchronous client in async function - in production, use proper async handling
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": full_prompt}]
            )
        )
        
        return response.content[0].text.strip()
    
    def _get_fallback_response(self) -> str:
        """Return a fallback response when AI generation fails"""
        fallback_responses = [
            "I'm having trouble processing that right now. Could you please rephrase your question?",
            "Let me think about that differently. Can you provide a bit more detail about what you're trying to accomplish?",
            "I want to make sure I understand correctly. Could you tell me more about your specific requirements?",
            "That's an interesting point. Can you help me understand the context a bit better?"
        ]
        
        import random
        return random.choice(fallback_responses)
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using AI"""
        prompt = f"""Extract entities (nouns representing people, things, or concepts) from this text and classify them:

Text: "{text}"

Return entities in this format:
- Entity name
- Type (person, object, concept, system)
- Brief description

Focus on domain-relevant entities that would be important for system specification."""

        try:
            response = await self.generate_response(prompt)
            # Parse response and structure it (simplified for now)
            return self._parse_entities_response(response)
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return []
    
    def _parse_entities_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response for entity extraction"""
        # Simplified parsing - in production, use more robust parsing
        entities = []
        lines = response.split('\n')
        
        for line in lines:
            if '-' in line and ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    name = parts[0].replace('-', '').strip()
                    description = parts[1].strip()
                    entities.append({
                        'name': name,
                        'type': 'entity',
                        'description': description
                    })
        
        return entities[:5]  # Limit to 5 entities per extraction