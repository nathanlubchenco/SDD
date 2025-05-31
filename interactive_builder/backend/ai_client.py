import os
import sys
import asyncio
from typing import List, Dict, Any, Optional

# Add the parent directory to Python path to import SDD core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

try:
    from src.core.ai_client import chat_completion, get_current_config
    USE_SDD_CLIENT = True
except ImportError:
    # Fallback to direct API clients if SDD modules not available
    import openai
    from anthropic import Anthropic
    USE_SDD_CLIENT = False
    print("Warning: Using fallback AI client. SDD core modules not found.")

class AIClient:
    """
    AI client that uses the same configuration as the main SDD project
    """
    
    def __init__(self):
        if USE_SDD_CLIENT:
            # Use SDD's configuration system
            config = get_current_config()
            self.provider = config['provider']
            self.model = config['model']
        else:
            # Fallback configuration
            self.provider = os.getenv('AI_PROVIDER', 'openai').lower()
            
            if self.provider == 'openai':
                self.openai_client = openai.AsyncOpenAI(
                    api_key=os.getenv('OPENAI_API_KEY')
                )
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
            elif self.provider == 'anthropic':
                self.anthropic_client = Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
                self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def generate_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate AI response using the configured provider
        """
        try:
            if USE_SDD_CLIENT:
                return await self._generate_sdd_response(prompt, conversation_history)
            else:
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
    
    async def _generate_sdd_response(
        self, 
        prompt: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate response using SDD's unified AI client"""
        
        # Build the conversation messages
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
        
        # Add recent conversation history for context
        if conversation_history:
            recent_history = conversation_history[-6:]  # Last 3 exchanges
            for exchange in recent_history:
                messages.append({
                    "role": exchange["role"],
                    "content": exchange["content"]
                })
        
        # Add the current prompt
        messages.append({
            "role": "user", 
            "content": prompt
        })
        
        # Use SDD's chat_completion function (which handles async internally)
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
        )
        
        return response.strip()
    
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