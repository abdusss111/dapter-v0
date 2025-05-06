from transcript import router as transcript_router
from main import app

app.include_router(transcript_router)