import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
import jwt

DB_PATH = "/tmp/users.json"
JWT_SECRET = os.getenv("JWT_SECRET", "codeforge-dev-secret-change-in-prod")
JWT_ALGO = "HS256"

def load_users():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(DB_PATH, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, password: str):
    users = load_users()
    email = email.lower().strip()
    if any(u["email"] == email for u in users):
        raise ValueError("Email already registered")
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow().isoformat()
    }
    users.append(user)
    save_users(users)
    return {"id": user["id"], "email": user["email"]}

def authenticate_user(email: str, password: str):
    users = load_users()
    email = email.lower().strip()
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    token = jwt.encode(
        {
            "sub": user["id"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(days=30)
        },
        JWT_SECRET,
        algorithm=JWT_ALGO
    )
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"]}
    }

def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])

def get_user_by_id(user_id: str):
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return None
    return {"id": user["id"], "email": user["email"]}
