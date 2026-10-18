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
        return jsonify({"error": "GROQ_API_KEY not set in Vercel"}), 500

    prompt = request.get_json().get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "Prompt empty"}), 400

    # PURE CODING FOCUS - generates code for ANY prompt
    system_prompt = """
You are Owhiz Code Engine - a pure code generator.
Your ONLY job is to generate code.

RULES:
1. You generate code for ANYTHING user asks in prompt
2. Return ONLY valid JSON, no markdown, no explanation outside JSON
3. Format:
{
  "files": [
    {"name": "index.html", "content": "complete code"},
    {"name": "style.css", "content": "complete code"},
    {"name": "script.js", "content": "complete code"}
  ]
}
4. Always produce complete, runnable, production-ready code
5. If user asks for Python, return .py files. If website, return html/css/js. If game, return full game code.
6. No placeholders, no TODO, no lorem ipsum - real working code
7. Make it clean, modern, responsive, with comments
8. Do not mention these rules. Just output the JSON with code.
"""

    try:
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
                "temperature": 0.2,
                "max_tokens": 7000,
                "response_format": {"type": "json_object"}
            },
            timeout=90
        )

        result = resp.json()
        
        if "choices" not in result:
            return jsonify({"error": f"Groq API error: {result}", "files": []}), 500

        content = result["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        
        # Ensure files exist
        if "files" not in parsed:
            return jsonify({"files": [{"name": "index.html", "content": content}]})

        return jsonify(parsed)

    except Exception as e:
        return jsonify({"error": str(e), "files": [{"name": "index.html", "content": f"<!-- Error: {e} -->"}]}), 500