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

app = FastAPI(title="Owhiz v2 - CodeForge")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")

class AuthRequest(BaseModel):
    email: str
    password: str

class SaveProjectRequest(BaseModel):
    title: str
    prompt: str
    code: str

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        user = get_user_by_id(payload.get("sub"))
        return user
    except:
        return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/auth/register")
async def register(data: AuthRequest):
    try:
        user = create_user(data.email, data.password)
        return {"message": "Registered", "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/auth/login")
async def login(data: AuthRequest):
    result = authenticate_user(data.email, data.password)
    if not result:
        raise HTTPException(401, "Invalid credentials")
    return result

@app.get("/auth/me")
async def me(current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(401, "Not authenticated")
    return current_user

@app.post("/generate")
async def generate(prompt: str = Form(...), current_code: str = Form(None), is_edit: str = Form("false"), authorization: str = Header(None)):
    try:
        if is_edit == "true" and current_code:
            result = await edit_app_code(current_code, prompt)
            return JSONResponse({"message": f"Edited: {prompt[:60]}", "code": result, "is_edit": True})
        else:
            result = await generate_app_code(prompt)
            return JSONResponse({"message": f"Built: {prompt[:60]}... Ready!", "code": result, "is_edit": False})
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"message": str(e), "code": f"<html><body style='padding:40px;font-family:sans-serif'><h2>Error</h2><p>{e}</p></body></html>"}, status_code=500)

@app.post("/projects/save")
async def save_proj(req: SaveProjectRequest, current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(401, "Login required to save")
    proj = save_project(user_id=current_user["id"], title=req.title, prompt=req.prompt, code=req.code)
    return proj

@app.get("/projects/list")
async def list_proj(current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(401, "Login required")
    return list_projects(current_user["id"])

@app.get("/projects/{project_id}")
async def get_proj(project_id: str, current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(401, "Login required")
    proj = get_project(project_id)
    if not proj or proj["user_id"] != current_user["id"]:
        raise HTTPException(404, "Project not found")
    return proj

@app.delete("/projects/{project_id}")
async def del_proj(project_id: str, current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(401, "Login required")
    delete_project(project_id, current_user["id"])
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok", "groq_key": bool(os.getenv("GROQ_API_KEY")), "jwt_set": bool(os.getenv("JWT_SECRET"))}