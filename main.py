from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import json

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.get_json().get('prompt', '')

    system_prompt = """
You are CodeForge Agent - a FREE Replit Agent clone.
User will ask to build anything: website, game, todo app, calculator, etc.
You must respond in VALID JSON only, with this format:
{
  "files": [
    {"name": "index.html", "content": "<html>..."},
    {"name": "style.css", "content": "..."},
    {"name": "script.js", "content": "..."}
  ],
  "explanation": "short explanation"
}
Generate complete working code. No placeholders. Make it runnable.
If user asks for Python, return main.py. If website, return html/css/js.
"""

    try:
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
        return jsonify({"error": str(e)}), 500