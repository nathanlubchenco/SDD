import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def chat_completion(messages, model="claude-3-5-sonnet-20241022", temperature=0.0, max_tokens=None):
    """
    Send a sequence of chat messages to the Anthropic API and return the assistant's response text.
    """
    params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    response = client.messages.create(**params)
    return response.content[0].text