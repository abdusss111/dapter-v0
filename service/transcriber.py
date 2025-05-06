# transcriber.py
import asyncio
import threading
import queue
from fastapi import WebSocket
from google.cloud import speech_v1p1beta1 as speech

speech_client = speech.SpeechClient()

def get_streaming_config():
    recognition_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="ru",
        enable_speaker_diarization=True,
        diarization_speaker_count=2,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=recognition_config,
        interim_results=True,
        single_utterance=False,
    )
    return streaming_config

def request_generator(audio_q):
    while True:
        chunk = audio_q.get()
        if chunk is None:
            break
        if isinstance(chunk, bytes) and len(chunk) > 0:
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

def run_transcription(ws: WebSocket, audio_q: queue.Queue, loop: asyncio.AbstractEventLoop, source: str):
    try:
        responses = speech_client.streaming_recognize(
            config=get_streaming_config(),
            requests=request_generator(audio_q)
        )

        last_transcript = ""
        for response in responses:
            for result in response.results:
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript.strip()
                final = result.is_final
                tag = (
                    result.alternatives[0].words[-1].speaker_tag
                    if result.alternatives[0].words
                    else None
                )

                if final or transcript != last_transcript:
                    last_transcript = transcript

                    print(f"[{source.upper()}] [{'✔️ FINAL' if final else '…'}] Speaker {tag or '?'}: {transcript}")

                    coro = ws.send_json({
                        "transcript": transcript,
                        "isFinal": final,
                        "speakerTag": tag,
                        "source": source,
                    })
                    asyncio.run_coroutine_threadsafe(coro, loop)

    except Exception as e:
        print("🔥 Transcription error:", e)
        try:
            loop.call_soon_threadsafe(asyncio.create_task, ws.close())
        except Exception as close_err:
            print("⚠️ Error closing socket:", close_err)
