import hashlib
import secrets
from typing import Optional, Dict
from app.core.database import get_db, dict_from_row

tokens: Dict[str, Dict] = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def generate_token() -> str:
    return secrets.token_urlsafe(32)

class AuthService:
    @staticmethod
    def register(username: str, password: str, role: str = "user") -> dict:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if c.fetchone():
                return {"error": "Username already exists", "status_code": 400}
            
            password_hash = hash_password(password)
            c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                      (username, password_hash, role))
            conn.commit()
            return {"user_id": c.lastrowid, "status_code": 201}
    
    @staticmethod
    def login(username: str, password: str) -> dict:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            
            if not row or not verify_password(password, dict_from_row(row)["password_hash"]):
                return {"error": "Invalid username or password", "status_code": 401}
            
            user = dict_from_row(row)
            token = generate_token()
            tokens[token] = {"user_id": user["id"], "username": user["username"], "role": user["role"]}
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "created_at": user.get("created_at", "")
                }
            }
    
    @staticmethod
    def logout(token: str):
        tokens.pop(token, None)
        return {"message": "Logged out successfully"}
    
    @staticmethod
    def get_current_user(token: str) -> Optional[Dict]:
        return tokens.get(token)
    
    @staticmethod
    def verify_token(authorization: str) -> Dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise Exception("Invalid authorization")
        
        token = authorization.replace("Bearer ", "")
        user = AuthService.get_current_user(token)
        if not user:
            raise Exception("Invalid token")
        
        return {"user": user, "token": token}