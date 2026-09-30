import requests

# ─── Configuration ────────────────────────────────────────────
# Replace these with your actual values
API_KEY      = "sk-l2_hig63a8xfXfhC1b1HzA"
LLM_ENDPOINT = "https://openai.generative.engine.capgemini.com/v1/chat/completions"  # e.g. https://api.openai.com/v1/chat/completions
MODEL        = "openai.gpt-4o"               # or whichever model your company engine uses

SYSTEM_PROMPT = "You are a helpful assistant."
# ──────────────────────────────────────────────────────────────


def chat_completion(messages: list[dict]) -> str:
    """
    Send messages to LLM and return response text.
    Simplified version - no budget tracking for POC.
    
    messages format:
    [
        {"role": "system",    "content": "You are a helpful assistant."},
        {"role": "user",      "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user",      "content": "How are you?"}   # latest message
    ]
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "x-api-key"    : API_KEY,
        "Content-Type" : "application/json",
    }

    payload = {
        "model"      : MODEL,
        "messages"   : messages,
        "temperature": 0.2,
        "max_tokens" : 1000,
    }

    try:
        response = requests.post(
            LLM_ENDPOINT,
            headers = headers,
            json    = payload,
            timeout = 120,
        )

        if response.status_code != 200:
            response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        return content

    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."

    except requests.exceptions.RequestException as e:
        return f"Error: Request failed - {str(e)}"

    except (KeyError, IndexError) as e:
        return f"Error: Unexpected response format - {str(e)}"