from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(prompt: str = Form(...)):
    groq_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You generate complete single-file HTML apps with inline CSS and JS. Return only HTML."},
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post(url, headers=headers, json=payload)
    result = r.json()
    code = result["choices"][0]["message"]["content"]
    return {"code": code, "message": f"Built: {prompt}"}