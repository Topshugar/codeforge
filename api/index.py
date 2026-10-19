import os, json, uuid, hashlib
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import jwt
from groq import Groq

app = FastAPI()
templates = Jinja2Templates(directory="templates")
JWT_SECRET = os.getenv("JWT_SECRET", "owhiz-secret-123")
DB_FILE = "/tmp/db.json"
USERS_FILE = "/tmp/users.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE) as f: return json.load(f)
    except: return {}
def save_db(d):
    with open(DB_FILE, "w") as f: json.dump(d, f)
def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE) as f: return json.load(f)
    except: return {}
def save_users(u):
    with open(USERS_FILE, "w") as f: json.dump(u, f)
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def generate_app_code(prompt):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    system = "You are expert web developer. Return ONLY single complete HTML file with inline CSS and JS. No explanation. Must be fully functional, modern, beautiful."
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
        temperature=0.7, max_tokens=8000
    )
    code = r.choices[0].message.content
    if "```html" in code: code = code.split("```html")[1].split("```")[0]
    elif "```" in code: code = code.split("```")[1].split("```")[0]
    return code

def edit_app_code(current, instruction):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    system = f"You are expert. Edit this HTML app per instruction. Return ONLY full edited HTML.\nCurrent code:\n{current[:15000]}"
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":system},{"role":"user","content":instruction}],
        temperature=0.6, max_tokens=8000
    )
    code = r.choices[0].message.content
    if "```html" in code: code = code.split("```html")[1].split("```")[0]
    elif "```" in code: code = code.split("```")[1].split("```")[0]
    return code

def get_user(token):
    try:
        p = jwt.decode(token.replace("Bearer ",""), JWT_SECRET, algorithms=["HS256"])
        users = load_users()
        for u in users.values():
            if u["id"]==p["sub"]: return u
    except: return None
    return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status":"ok","groq_set":bool(os.getenv("GROQ_API_KEY")),"jwt_set":bool(os.getenv("JWT_SECRET"))}

@app.post("/auth/register")
async def reg(d: dict):
    users=load_users()
    if d["email"] in users: raise HTTPException(400,"exists")
    uid=str(uuid.uuid4())
    users[d["email"]]={"id":uid,"email":d["email"],"password":hash_pw(d["password"])}
    save_users(users)
    return {"id":uid,"email":d["email"]}

@app.post("/auth/login")
async def login(d: dict):
    users=load_users()
    u=users.get(d["email"])
    if not u or u["password"]!=hash_pw(d["password"]): raise HTTPException(401,"bad")
    token=jwt.encode({"sub":u["id"],"email":u["email"],"exp":datetime.utcnow()+timedelta(days=7)},JWT_SECRET,algorithm="HS256")
    return {"token":token,"user":{"id":u["id"],"email":u["email"]}}

@app.get("/auth/me")
async def me(authorization: str = Header(None)):
    if not authorization: raise HTTPException(401,"no token")
    u=get_user(authorization)
    if not u: raise HTTPException(401,"bad")
    return {"id":u["id"],"email":u["email"]}

@app.post("/generate")
async def gen(prompt: str=Form(...), current_code: str=Form(None), is_edit: str=Form("false")):
    try:
        if is_edit=="true" and current_code:
            code=edit_app_code(current_code,prompt)
        else:
            code=generate_app_code(prompt)
        return {"code":code,"message":"Done"}
    except Exception as e:
        raise HTTPException(500,str(e))

@app.post("/projects/save")
async def savep(d: dict, authorization: str=Header(None)):
    u=get_user(authorization)
    if not u: raise HTTPException(401,"login")
    db=load_db()
    if u["id"] not in db: db[u["id"]]={}
    pid=str(uuid.uuid4())
    db[u["id"]][pid]={"id":pid,"user_id":u["id"],"title":d["title"],"prompt":d["prompt"],"code":d["code"],"created_at":datetime.utcnow().isoformat()}
    save_db(db)
    return {"ok":True}

@app.get("/projects/list")
async def listp(authorization: str=Header(None)):
    u=get_user(authorization)
    if not u: raise HTTPException(401,"login")
    db=load_db()
    return list(db.get(u["id"],{}).values())[::-1]

@app.get("/projects/{pid}")
async def getp(pid: str, authorization: str=Header(None)):
    u=get_user(authorization)
    db=load_db()
    return db.get(u["id"],{}).get(pid)

@app.delete("/projects/{pid}")
async def delp(pid: str, authorization: str=Header(None)):
    u=get_user(authorization)
    db=load_db()
    if u["id"] in db and pid in db[u["id"]]:
        del db[u["id"]][pid]
        save_db(db)
    return {"ok":True}
