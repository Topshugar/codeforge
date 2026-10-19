# Owhiz v2 - CodeForge

Build anything with AI. Free Groq Llama 3.3 70B.

## Features
- Build complete HTML apps from prompt
- Edit mode - modify existing apps
- Auth - login/register with JWT
- Save projects
- Download / New Tab preview
- Deployed on Vercel

## Tech
FastAPI + Jinja2 + Groq + JWT + Vercel

## Env Vars (Vercel)
GROQ_API_KEY=your_groq_key
JWT_SECRET=any_random_string_32_chars

## Run Local
pip install -r requirements.txt
uvicorn main:app --reload

## API
POST /generate - prompt, current_code, is_edit
POST /auth/register
POST /auth/login
GET /auth/me
POST /projects/save
GET /projects/list
GET /projects/{id}
DELETE /projects/{id}
GET /health

## Deploy
Push to GitHub -> Import to Vercel -> Add Env Vars -> Deploy