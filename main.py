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
        return jsonify({"reply": "GROQ_API_KEY not set. Add it in Vercel > Settings > Env Vars"}), 500

    data = request.get_json()
    user_msg = data.get('message', '').strip()
    history = data.get('history', [])

    system = """You are Owhiz - a friendly, expert Build Agent.

Your job:
- You engage in dialogue like Replit Agent
- You provide recommendations
- You guide users to formulate better prompts
- You help build sophisticated apps/websites

Rules:
1. If user prompt is vague (e.g. "build school website"), ASK 2-3 clarifying questions and suggest features: e.g. Admissions, Courses, Student Portal, Dark mode, Payment.
2. If user prompt is clear, say "Great, building that now..." and provide a refined, detailed prompt for generation.
3. Be concise, friendly, helpful. Like a senior dev guiding a junior.
4. Always end with either a question OR with [READY_TO_BUILD] + the refined prompt.
5. You are pure coding agent. Focus only on building.

Format when ready:
[READY_TO_BUILD]
Build: <refined detailed prompt>

Example:
User: build school website
You: Nice idea! To make it sophisticated, I recommend:
1. Hero with admissions CTA
2. Courses section with filters
3. Teachers, testimonials, contact + map
4. Should I add student login or fee payment?

What type of school and colors do you prefer?

If user says "add login", you refine and say READY.
"""

    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_msg})

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 1000},
            timeout=30)
        reply = r.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {e}"}), 500

@app.route('/generate', methods=['POST'])
def generate():
    api_key = os.environ.get("GROQ_API_KEY")
    prompt = request.get_json().get('prompt', '')

    system = """You are Owhiz Builder Engine. Generate complete, production-ready code for ANY prompt.

Return ONLY valid JSON:
{
  "files": [
    {"name": "index.html", "content": "FULL WORKING CODE"},
    {"name": "style.css", "content": "..."},
    {"name": "script.js", "content": "..."}
  ]
}

Rules: No TODO, no placeholders, responsive, modern animations, beautiful. Always include index.html."""

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0.3, "max_tokens": 7000,
                "response_format": {"type": "json_object"}
            }, timeout=90)
        content = r.json()["choices"][0]["message"]["content"]
        return jsonify(json.loads(content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500