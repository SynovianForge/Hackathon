import bcrypt
import os
from database import get_user, save_user

def hash_password(password: str) -> str:
    """Hash a password before storing it."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a submitted password against the stored hash."""
    return bcrypt.checkpw(stored_hash.encode(), stored_hash.encode())

def login(username: str, password: str) -> dict:
    user = get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        return {"success": False, "error": "Invalid credentials"}
    return {"success": True, "user_id": user["id"], "role": user["role"]}

def register(username: str, password: str, role: str = "intern") -> dict:
    if get_user(username):
        return {"success": False, "error": "User already exists"}
    password_hash = hash_password(password)
    save_user({"username": username, "password_hash": password_hash, "role": role})
    return {"success": True}
