from flask import Flask, render_template, request, jsonify
import os, json, requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"reply": "GROQ_API_KEY not set in Vercel Env Vars"}), 200

    data = request.get_json()
    user_msg = data.get('message', '').strip()
    history = data.get('history', [])

    system = """You are Owhiz Agent - Build Agent.
If prompt vague, ask 2-3 questions and suggest features.
If clear, end with [READY_TO_BUILD] + refined detailed prompt.
Be concise."""

    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_msg})

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 1000},
            timeout=30)
        j = r.json()
        if "error" in j:
            return jsonify({"reply": f"Groq Error: {j['error'].get('message','')}"}), 200
        if "choices" not in j:
            return jsonify({"reply": f"API Error: {str(j)[:300]}"}), 200
        reply = j["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Server Error: {e}"}), 200

@app.route('/generate', methods=['POST'])
def generate():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "No API key"}), 500
    prompt = request.get_json().get('prompt', '')
    system = """Return ONLY valid JSON: {"files":[{"name":"index.html","content":"FULL CODE"}]}. Modern, responsive, no placeholders."""

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0.3, "max_tokens": 7000,
                "response_format": {"type": "json_object"}
            }, timeout=90)
        j = r.json()
        if "error" in j:
            return jsonify({"error": j["error"].get("message")}), 500
        content = j["choices"][0]["message"]["content"]
        return jsonify(json.loads(content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500