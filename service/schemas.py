# schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TranscriptOut(BaseModel):
    id: int
    title: Optional[str]
    content: str
    speaker_json: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
