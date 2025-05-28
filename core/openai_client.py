import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_completion(messages, model="gpt-4", temperature=0.0, max_tokens=None):
    """
    Send a sequence of chat messages to the OpenAI API and return the assistant's response text.
    """
    params = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    response = client.chat.completions.create(**params)
    return response.choices[0].message.content
