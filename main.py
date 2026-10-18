from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os, json, re, requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

SYSTEM_PROMPT = """You are CodeForge Agent, a Replit Agent clone.
Output ONLY valid JSON:
{
  "plan": "short plan",
  "files": [
    {"name": "index.html", "content": "full html with Tailwind https://cdn.tailwindcss.com"},
    {"name": "style.css", "content": "css if needed"},
    {"name": "script.js", "content": "js if needed"}
  ]
}
Rules: 2-4 files, beautiful, working, no text outside JSON.
Build ANYTHING user asks - trading app, calculator, clone, dashboard, anything.
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...), existing: str = Form("")):
    try:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return JSONResponse({"error": "GROQ_API_KEY missing in Vercel > Settings > Environment Variables"})

        user_msg = f"Build this: {prompt}"
        if existing and existing != "[]":
            user_msg = f"Existing files: {existing[:4000]}\n\nEdit request: {prompt}\nReturn FULL updated files."

        # Direct HTTP call - bypasses broken SDK
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.35,
                "max_tokens": 8000
            },
            timeout=60
        )
        
        if resp.status_code != 200:
            return JSONResponse({"error": f"Groq API Error {resp.status_code}: {resp.text[:500]}"})
        
        raw = resp.json()["choices"][0]["message"]["content"]
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            raw = m.group(0)
        
        data = json.loads(raw)
        return data

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)})