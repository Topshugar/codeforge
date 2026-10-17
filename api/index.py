from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
import os, json, re

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)

SYSTEM_PROMPT = """You are CodeForge. Output ONLY valid JSON: {"files": [{"name": "index.html", "content": "<full html>"}]}. Make index.html full working standalone, beautiful, responsive. Use Tailwind CDN."""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...)):
    try:
        client = get_client()
        if not client:
            return JSONResponse({"error": "GROQ_API_KEY missing"}, status_code=500)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Build: {prompt}. JSON only."}
            ],
            temperature=0.3,
            max_tokens=7000
        )
        raw = completion.choices[0].message.content
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        data = json.loads(raw)
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)