from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
import os, json, re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)

SYSTEM_PROMPT = """You are CodeForge Agent, a Replit Agent clone.

You build COMPLETE multi-file web apps.

Output ONLY valid JSON:
{
  "plan": "short 1 line plan",
  "files": [
    {"name": "index.html", "content": "full file content"},
    {"name": "style.css", "content": "full css"},
    {"name": "script.js", "content": "full js"}
  ]
}

Rules:
- Always return 2-4 files minimum for real apps
- index.html must link style.css and script.js
- Make it BEAUTIFUL like Replit apps - modern, Tailwind CDN: https://cdn.tailwindcss.com
- Fully working, no placeholders
- Mobile responsive
- No text outside JSON
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...), existing: str = Form("")):
    try:
        client = get_client()
        if not client:
            return JSONResponse({"error": "GROQ_API_KEY missing in Vercel"})

        user_msg = f"Build this: {prompt}"
        if existing:
            user_msg = f"Existing files: {existing}\n\nEdit request: {prompt}\n\nReturn FULL updated files."

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg + " JSON only."}
            ],
            temperature=0.35,
            max_tokens=9000
        )
        raw = completion.choices[0].message.content
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        try:
            data = json.loads(raw)
            return data
        except:
            return {"plan": "Built single file", "files": [{"name": "index.html", "content": raw}]}
    except Exception as e:
        return JSONResponse({"error": str(e)})