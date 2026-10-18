from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Import inside route so Vercel doesn't crash on start
    try:
        from groq import Groq
    except Exception as e:
        return jsonify({"error": f"Groq not installed: {e}"}), 500

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return jsonify({"error": "GROQ_API_KEY not set in Vercel env vars"}), 500

    prompt = request.get_json().get('prompt', '')
    
    system_prompt = """You are CodeForge Agent. Respond in VALID JSON only:
{"files": [{"name": "index.html", "content": "..."}, {"name": "style.css", "content": "..."}, {"name": "script.js", "content": "..."}], "explanation": "..."}
Generate complete working code."""

    try:
        client = Groq(api_key=api_key)
        res = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=6000,
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "files": [{"name": "error.txt", "content": str(e)}]}), 500