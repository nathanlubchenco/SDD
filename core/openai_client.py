import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_completion(messages, model="gpt-4.1", temperature=0.0, max_tokens=None):
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
    response = openai.ChatCompletion.create(**params)
    return response.choices[0].message.content

def completion(prompt, model="gpt-4.1", temperature=0.0, max_tokens=None):
    """
    Send a completion prompt to the OpenAI API and return the generated text.
    """
    params = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
    }
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    response = openai.Completion.create(**params)
    return response.choices[0].text
