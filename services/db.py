import os
import json
import uuid
from datetime import datetime

DB_PATH = "/tmp/projects.json"

def load_projects():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return []

def save_all(projects):
    with open(DB_PATH, "w") as f:
        json.dump(projects, f, indent=2)

def save_project(user_id: str, title: str, prompt: str, code: str):
    projects = load_projects()
    project = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title[:80],
        "prompt": prompt,
        "code": code,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    projects.insert(0, project)
    save_all(projects)
    return project

def list_projects(user_id: str):
    projects = load_projects()
    return [p for p in projects if p["user_id"] == user_id]

def get_project(project_id: str):
    projects = load_projects()
    return next((p for p in projects if p["id"] == project_id), None)

def delete_project(project_id: str, user_id: str):
    projects = load_projects()
    filtered = [p for p in projects if not (p["id"] == project_id and p["user_id"] == user_id)]
    if len(filtered) != len(projects):
        save_all(filtered)
        return True
    return False
