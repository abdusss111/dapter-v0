# transcript.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import verify_google_token, oauth2_scheme
from deps import get_db
from models import Transcript, User
from schemas import TranscriptOut

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_google_token(token)  # ✅ Verifies with Google

    user_id = payload["sub"]
    email = payload["email"]
    name = payload.get("name", "")

    # ✅ Find or create user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

router = APIRouter()

@router.get("/api/transcripts", response_model=list[TranscriptOut])
def list_transcripts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ Use injected user
):
    transcripts = db.query(Transcript).filter(Transcript.user_id == user.id).all()
    return transcripts


@router.get("/api/transcripts/{transcript_id}", response_model=TranscriptOut)
def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ Use injected user
):
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == user.id
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return transcript
