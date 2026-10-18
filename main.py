import os
from fastapi import FastAPI, Form, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from services.groq_service import generate_app_code, edit_app_code
from services.auth_service import create_user, authenticate_user, decode_token, get_user_by_id
from services.db import save_project, list_projects, get_project, delete_project
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Owhiz v2 - CodeForge", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class AuthRequest(BaseModel):
    email: str
    password: str

class SaveProjectRequest(BaseModel):
    title: str
    prompt: str
    code: str

def get_current_user_optional(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = decode_token(token)
        user = get_user_by_id(payload.get("sub"))
        return user
    except Exception:
        return None

def get_current_user_required(authorization: Optional[str] = Header(None)):
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/auth/register")
async def register(data: AuthRequest):
    if len(data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    try:
        user = create_user(data.email, data.password)
        return {"message": "Registered", "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/auth/login")
async def login(data: AuthRequest):
    result = authenticate_user(data.email, data.password)
    if not result:
        raise HTTPException(401, "Invalid email or password")
    return result

@app.get("/auth/me")
async def me(current_user = Depends(get_current_user_required)):
    return current_user

@app.post("/generate")
async def generate(
    prompt: str = Form(...),
    current_code: str = Form(None),
    is_edit: str = Form("false")
):
    if not prompt.strip():
        raise HTTPException(400, "Prompt cannot be empty")
    
    try:
        if is_edit.lower() == "true" and current_code and len(current_code.strip()) > 100:
            result = await edit_app_code(current_code, prompt)
            return JSONResponse({"message": f"✏️ Edited: {prompt[:70]}", "code": result, "is_edit": True})
        else:
            result = await generate_app_code(prompt)
            return JSONResponse({"message": f"⚡ Built: {prompt[:70]}... App ready!", "code": result, "is_edit": False})
    except ValueError as ve:
        # Missing API key
        return JSONResponse({"message": str(ve), "code": f"<html><body style='font-family:Inter,sans-serif;padding:40px'><h2 style='color:#ef4444'>Config Error</h2><p>{ve}</p><p>Set GROQ_API_KEY in Vercel > Settings > Environment Variables</p></body></html>"}, status_code=500)
    except Exception as e:
        print(f"[CodeForge Error] {e}")
        return JSONResponse({"message": f"Generation failed: {str(e)}", "code": f"<html><body style='padding:40px;font-family:sans-serif'><h2>Build Failed</h2><p>{str(e)}</p><p style='color:#64748b'>Try a simpler prompt or check Groq rate limits</p></body></html>"}, status_code=500)

@app.post("/projects/save")
async def save_proj(req: SaveProjectRequest, current_user = Depends(get_current_user_required)):
    proj = save_project(user_id=current_user["id"], title=req.title, prompt=req.prompt, code=req.code)
    return proj

@app.get("/projects/list")
async def list_proj(current_user = Depends(get_current_user_required)):
    return list_projects(current_user["id"])

@app.get("/projects/{project_id}")
async def get_proj(project_id: str, current_user = Depends(get_current_user_required)):
    proj = get_project(project_id)
    if not proj or proj["user_id"] != current_user["id"]:
        raise HTTPException(404, "Project not found")
    return proj

@app.delete("/projects/{project_id}")
async def del_proj(project_id: str, current_user = Depends(get_current_user_required)):
    delete_project(project_id, current_user["id"])
    return {"ok": True}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "groq_key_set": bool(os.getenv("GROQ_API_KEY")),
        "jwt_set": bool(os.getenv("JWT_SECRET")),
        "model": "llama-3.3-70b-versatile"
    }