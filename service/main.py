from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
import queue, threading, asyncio
from requests import Session
from transcriber import run_transcription
from deps import get_db
from sqlalchemy import text
app = FastAPI()

@app.websocket("/ws/transcribe/{source}")
async def websocket_transcribe(ws: WebSocket, source: str):
    await ws.accept()
    audio_q = queue.Queue()

    loop = asyncio.get_running_loop()
    threading.Thread(target=run_transcription, args=(ws, audio_q, loop, source), daemon=True).start()

    try:
        while True:
            data = await ws.receive_bytes()
            if isinstance(data, bytes) and len(data) > 0:
                audio_q.put(data)
            else:
                print("⚠️ Skipped invalid incoming audio")
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
    finally:
        audio_q.put(None)

@app.get("/ping-db/")
async def ping_db(db: Session = Depends(get_db)):
    try:
        db.execute(text('SELECT 1'))
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}