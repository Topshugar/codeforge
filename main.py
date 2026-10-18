from flask import Flask, render_template, request, jsonify
import os
import json
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "GROQ_API_KEY not set"}), 500

    data = request.get_json()
    prompt = data.get('prompt', '')

    system_prompt = """You are CodeForge Agent. You MUST respond in VALID JSON only with this format:
{"files": [{"name": "index.html", "content": "<html>... complete code"}, {"name": "style.css", "content": "..."}, {"name": "script.js", "content": "..."}], "explanation": "short"}
Generate complete working code. No placeholders."""

    try:
        # Direct API call - no Groq library needed
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 6000,
                "response_format": {"type": "json_object"}
            },
            timeout=60
        )
        
        result = resp.json()
        if "error" in result:
            return jsonify({"error": str(result["error"])}), 500
            
        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return jsonify(parsed)

    except Exception as e:
        return jsonify({"error": str(e), "files": [{"name": "error.txt", "content": str(e)}]}), 500