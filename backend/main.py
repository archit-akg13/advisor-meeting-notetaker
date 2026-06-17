"""FastAPI backend for Advisor Meeting AI Notetaker."""

import os
import json
import time
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from transcribe import transcribe_audio, extract_audio_from_video
from extract import extract_meeting_data
from compliance import run_compliance_check
from formatter import format_crm_note, format_compliance_panel

load_dotenv()

app = FastAPI(
    title="Advisor Meeting AI Notetaker",
    description="Turns advisor client-meeting recordings into compliant, CRM-ready notes with SEC/FINRA suitability checks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".mp4", ".ogg", ".flac"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@app.get("/")
async def root():
    return {
        "name": "Advisor Meeting AI Notetaker",
        "version": "1.0.0",
        "description": "Upload a meeting recording, get compliant CRM notes in 30 seconds",
        "endpoints": {
            "POST /process": "Upload audio file for full processing",
            "POST /transcribe": "Transcribe audio only",
            "POST /analyze": "Analyze existing transcript text",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/process")
async def process_meeting(
    file: UploadFile = File(...),
    provider: str = "openrouter",
    whisper_model: str = "base"
):
    """Full pipeline: audio â transcript â extraction â compliance â CRM note.

    Args:
        file: Audio or video file (.mp3, .wav, .m4a, .webm, .mp4)
        provider: LLM provider for extraction ('openai' or 'anthropic')
        whisper_model: Whisper model size (tiny, base, small, medium, large)
    """
    start_time = time.time()

    # Validate file
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Save uploaded file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Step 1: Transcribe
        audio_path = tmp_path
        if ext in {".mp4", ".webm"}:
            audio_path = extract_audio_from_video(tmp_path)

        transcript_result = transcribe_audio(audio_path, model_size=whisper_model)

        # Step 2: Extract structured data
        meeting_data = await extract_meeting_data(transcript_result["text"], provider=provider)

        # Step 3: Run compliance checks
        compliance_report = run_compliance_check(meeting_data)

        # Step 4: Format outputs
        crm_note = format_crm_note(meeting_data, compliance_report)
        compliance_panel = format_compliance_panel(compliance_report)

        processing_time = round(time.time() - start_time, 1)

        return JSONResponse({
            "status": "success",
            "processing_time_seconds": processing_time,
            "transcript": {
                "text": transcript_result["text"],
                "segments": transcript_result["segments"],
                "duration": transcript_result["duration"]
            },
            "meeting_data": meeting_data,
            "compliance": compliance_panel,
            "crm_note": crm_note,
            "metadata": {
                "filename": file.filename,
                "provider": provider,
                "whisper_model": whisper_model
            }
        })

    finally:
        os.unlink(tmp_path)
        if ext in {".mp4", ".webm"} and audio_path != tmp_path:
            os.unlink(audio_path)


@app.post("/transcribe")
async def transcribe_only(
    file: UploadFile = File(...),
    whisper_model: str = "base"
):
    """Transcribe audio file only, no analysis."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = transcribe_audio(tmp_path, model_size=whisper_model)
        return JSONResponse({"status": "success", "transcript": result})
    finally:
        os.unlink(tmp_path)


@app.post("/analyze")
async def analyze_transcript(
    transcript: str,
    provider: str = "openrouter"
):
    """Analyze an existing transcript (no audio processing).

    Send transcript text directly for extraction + compliance check.
    """
    start_time = time.time()

    meeting_data = await extract_meeting_data(transcript, provider=provider)
    compliance_report = run_compliance_check(meeting_data)
    crm_note = format_crm_note(meeting_data, compliance_report)
    compliance_panel = format_compliance_panel(compliance_report)

    return JSONResponse({
        "status": "success",
        "processing_time_seconds": round(time.time() - start_time, 1),
        "meeting_data": meeting_data,
        "compliance": compliance_panel,
        "crm_note": crm_note
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
