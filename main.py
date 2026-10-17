from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
import os, json, re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("Missing GROQ_API_KEY")
    return Groq(api_key=key)

SYSTEM_PROMPT = """You are CodeForge, a Replit Agent clone. User gives prompt like 'build todo app'. You must output ONLY valid JSON with files. Format: {"files": [{"name": "index.html", "content": "<full html>"}, {"name": "style.css", "content": ""}, {"name": "script.js", "content": ""}]} Rules: index.html must be FULL working standalone file with inline CSS/JS if possible Make it modern, beautiful, mobile responsive No explanation outside JSON Use Tailwind CDN if needed: https://cdn.tailwindcss.com"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...)):
    client = get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Build this: {prompt}. Output JSON only."}
        ],
        temperature=0.3,
        max_tokens=8000
    )
    raw = completion.choices[0].message.content
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        data = json.loads(raw)
        return data
    except:
        return {"files": [{"name": "index.html", "content": raw}]}