from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os, json, re, requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...)):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return JSONResponse({"error": "Missing GROQ_API_KEY in Vercel env vars. Add it in Settings > Environment Variables"})
    
    try:
        system_prompt = """You are CodeForge Agent. You build ANY web app user asks for.
Output ONLY valid JSON: {"plan": "short 1-line plan", "files": [{"name": "index.html", "content": "COMPLETE HTML with Tailwind CDN https://cdn.tailwindcss.com, fully working, beautiful, mobile responsive"}]}
Build ANYTHING: trading calculators, Instagram clones, dashboards, shops, landing pages. No text outside JSON."""

        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.35,
                "max_tokens": 8000
            },
            timeout=60
        )

        if resp.status_code != 200:
            return JSONResponse({"error": f"Groq API {resp.status_code}: {resp.text[:500]}"})

        raw = resp.json()["choices"][0]["message"]["content"]
        # extract json
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        
        data = json.loads(raw)
        return data

    except Exception as e:
        return JSONResponse({"error": str(e)})