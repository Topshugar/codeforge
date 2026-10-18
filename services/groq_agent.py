import os
import requests

def generate_app(prompt: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You generate complete single-file HTML apps with inline CSS and JS. Return only HTML."},
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post(url, headers=headers, json=payload)
    result = r.json()
    return result["choices"][0]["message"]["content"]