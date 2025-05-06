# auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from sqlalchemy.orm import Session
from deps import get_db
from models import User
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
oauth2_scheme = HTTPBearer()

def verify_google_token(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        return {
            "sub": idinfo["sub"],  # User's unique ID
            "email": idinfo["email"],
            "name": idinfo.get("name", "")
        }
    except Exception as e:
        print("Invalid token:", e)
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_google_token(token)
    user_id = payload["sub"]

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=payload["email"], name=payload["name"])
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
