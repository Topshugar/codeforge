from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os, json, re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_client():
    # Remove Vercel proxy vars that break Groq SDK
    for k in ["HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy","NO_PROXY","no_proxy"]:
        os.environ.pop(k, None)
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    # Import here after cleaning env
    from groq import Groq
    return Groq(api_key=key)

SYSTEM_PROMPT = """You are CodeForge Agent, a Replit Agent clone.
Output ONLY valid JSON:
{
  "plan": "short plan",
  "files": [
    {"name": "index.html", "content": "full file"},
    {"name": "style.css", "content": "css"},
    {"name": "script.js", "content": "js"}
  ]
}
Rules:
- 2-4 files minimum
- index.html must be complete with Tailwind CDN https://cdn.tailwindcss.com
- Beautiful modern UI
- Fully working logic, no placeholder
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
            return JSONResponse({"error": "GROQ_API_KEY missing in Vercel Env Vars"})

        user_msg = f"Build this: {prompt}"
        if existing and existing != "[]":
            user_msg = f"Existing files: {existing[:3000]}\n\nEdit request: {prompt}\nReturn FULL updated files."

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.35,
            max_tokens=8000
        )
        raw = completion.choices[0].message.content.strip()
        # extract json
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            raw = m.group(0)
        data = json.loads(raw)
        return data
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)})