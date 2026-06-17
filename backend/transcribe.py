"""Audio transcription using OpenAI Whisper."""

import os
import tempfile
import subprocess
from pathlib import Path


def transcribe_audio(file_path: str, model_size: str = "base") -> dict:
    """Transcribe audio file using Whisper.

    Args:
        file_path: Path to audio file (.mp3, .wav, .m4a, .webm)
        model_size: Whisper model size (tiny, base, small, medium, large)

    Returns:
        dict with 'text' (full transcript) and 'segments' (timestamped chunks)
    """
    import whisper

    model = whisper.load_model(model_size)
    result = model.transcribe(file_path, language="en", verbose=False)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip()
        })

    return {
        "text": result["text"].strip(),
        "segments": segments,
        "language": result.get("language", "en"),
        "duration": segments[-1]["end"] if segments else 0
    }


def extract_audio_from_video(video_path: str) -> str:
    """Extract audio track from video file using ffmpeg."""
    output_path = tempfile.mktemp(suffix=".wav")
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
         "-ar", "16000", "-ac", "1", output_path, "-y"],
        capture_output=True, check=True
    )
    return output_path
