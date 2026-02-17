"""Audio and video transcription plugin.

Provides speech-to-text transcription for audio and video files using
OpenAI's Whisper model (runs locally, no API key needed).

Requires ``openai-whisper`` (optional, fails gracefully at runtime).
For video files, ``ffmpeg`` must be installed on the system.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ...plugins.base import TransformerPlugin
from ...safety import check_read_path, check_write_path
from ...skill import skill, ConfigParam, ConfigScope, RiskLevel


def _check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _extract_audio(video_path: str, audio_path: str) -> Optional[str]:
    """Extract audio from a video file using ffmpeg. Returns error or None."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                "-y", audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return f"ffmpeg error: {result.stderr[:200]}"
        return None
    except FileNotFoundError:
        return "ffmpeg is not installed. Install it with: apt install ffmpeg (Linux) / brew install ffmpeg (Mac)"
    except subprocess.TimeoutExpired:
        return "ffmpeg timed out (>5 minutes). File may be too large."


_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus"}
_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".ts"}


@skill(
    name="audio_to_text",
    description="Transcribe an audio file to text using OpenAI Whisper (runs locally).",
    category="transcription",
    tags=["audio", "transcribe", "speech", "whisper", "convert"],
    idempotent=True,
    requires_filesystem=True,
    required_imports=["whisper"],
    display_name="Audio to Text",
    icon="mic",
    risk_level=RiskLevel.SAFE,
    group="Transcription",
    config_params=[
        ConfigParam(
            name="default_model",
            display_name="Whisper Model",
            description="Whisper model size to use for transcription.",
            type="select",
            default="base",
            options=["tiny", "base", "small", "medium", "large"],
        ),
    ],
)
def audio_to_text(
    input: str,
    model: str = "base",
    language: Optional[str] = None,
    output: str = "",
) -> dict:
    """Transcribe an audio file to text.

    Args:
        input: Path to the audio file (.wav, .mp3, .flac, .ogg, .m4a, etc.).
        model: Whisper model size: tiny, base, small, medium, large (default "base").
        language: Language code (e.g. "en", "es"). Auto-detected if not specified.
        output: Optional path to save transcription as .txt file.
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}

    try:
        import whisper
    except ImportError:
        return {
            "error": "openai-whisper is required. Install with: pip install openai-whisper"
        }

    try:
        whisper_model = whisper.load_model(model)
    except Exception as e:
        return {"error": f"Failed to load Whisper model '{model}': {e}"}

    options = {}
    if language:
        options["language"] = language

    try:
        result = whisper_model.transcribe(str(p), **options)
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}

    text = result.get("text", "").strip()
    detected_lang = result.get("language", "unknown")

    # Build segments summary
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip(),
        })

    # Save to file if requested
    if output:
        output = check_write_path(output)
        Path(output).write_text(text, encoding="utf-8")

    response = {
        "input": str(p),
        "text": text,
        "language": detected_lang,
        "model": model,
        "word_count": len(text.split()),
        "segment_count": len(segments),
        "success": True,
    }
    if output:
        response["output"] = output
    return response


@skill(
    name="video_to_text",
    description="Transcribe a video file to text by extracting audio and running Whisper.",
    category="transcription",
    tags=["video", "audio", "transcribe", "speech", "whisper", "convert"],
    idempotent=True,
    requires_filesystem=True,
    required_imports=["whisper"],
    display_name="Video to Text",
    icon="video",
    risk_level=RiskLevel.SAFE,
    group="Transcription",
    config_params=[
        ConfigParam(
            name="default_model",
            display_name="Whisper Model",
            description="Whisper model size to use for transcription.",
            type="select",
            default="base",
            options=["tiny", "base", "small", "medium", "large"],
        ),
    ],
)
def video_to_text(
    input: str,
    model: str = "base",
    language: Optional[str] = None,
    output: str = "",
) -> dict:
    """Transcribe a video file to text.

    Extracts audio from the video using ffmpeg, then transcribes with Whisper.

    Args:
        input: Path to the video file (.mp4, .mkv, .avi, .mov, .webm, etc.).
        model: Whisper model size: tiny, base, small, medium, large (default "base").
        language: Language code (e.g. "en", "es"). Auto-detected if not specified.
        output: Optional path to save transcription as .txt file.
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}

    if not _check_ffmpeg():
        return {
            "error": "ffmpeg is required for video transcription. "
            "Install with: apt install ffmpeg (Linux) / brew install ffmpeg (Mac)"
        }

    try:
        import whisper
    except ImportError:
        return {
            "error": "openai-whisper is required. Install with: pip install openai-whisper"
        }

    # Extract audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_audio = tmp.name

    try:
        err = _extract_audio(str(p), tmp_audio)
        if err:
            return {"error": err}

        whisper_model = whisper.load_model(model)

        options = {}
        if language:
            options["language"] = language

        result = whisper_model.transcribe(tmp_audio, **options)
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}
    finally:
        Path(tmp_audio).unlink(missing_ok=True)

    text = result.get("text", "").strip()
    detected_lang = result.get("language", "unknown")

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 1),
            "end": round(seg["end"], 1),
            "text": seg["text"].strip(),
        })

    if output:
        output = check_write_path(output)
        Path(output).write_text(text, encoding="utf-8")

    response = {
        "input": str(p),
        "text": text,
        "language": detected_lang,
        "model": model,
        "word_count": len(text.split()),
        "segment_count": len(segments),
        "success": True,
    }
    if output:
        response["output"] = output
    return response


@skill(
    name="video_to_subtitles",
    description="Generate SRT subtitles from a video or audio file using Whisper.",
    category="transcription",
    tags=["video", "audio", "subtitles", "srt", "whisper", "convert"],
    side_effects=True,
    requires_filesystem=True,
    required_imports=["whisper"],
    display_name="Video to Subtitles",
    icon="subtitles",
    risk_level=RiskLevel.MODERATE,
    group="Transcription",
)
def video_to_subtitles(
    input: str,
    output: str = "",
    model: str = "base",
    language: Optional[str] = None,
) -> dict:
    """Generate SRT subtitles from a video or audio file.

    Args:
        input: Path to the video or audio file.
        output: Path for the output .srt file (defaults to same name with .srt extension).
        model: Whisper model size: tiny, base, small, medium, large (default "base").
        language: Language code (e.g. "en", "es"). Auto-detected if not specified.
    """
    input = check_read_path(input)
    p = Path(input)
    if not p.exists():
        return {"error": f"File not found: {input}"}
    if not output:
        output = str(p.with_suffix(".srt"))
    output = check_write_path(output)

    try:
        import whisper
    except ImportError:
        return {
            "error": "openai-whisper is required. Install with: pip install openai-whisper"
        }

    is_video = p.suffix.lower() in _VIDEO_EXTENSIONS
    tmp_audio = None

    try:
        source = str(p)

        # Extract audio from video if needed
        if is_video:
            if not _check_ffmpeg():
                return {
                    "error": "ffmpeg is required for video files. "
                    "Install with: apt install ffmpeg (Linux) / brew install ffmpeg (Mac)"
                }
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_audio = tmp.name
            err = _extract_audio(str(p), tmp_audio)
            if err:
                return {"error": err}
            source = tmp_audio

        whisper_model = whisper.load_model(model)
        options = {}
        if language:
            options["language"] = language

        result = whisper_model.transcribe(source, **options)
    except Exception as e:
        return {"error": f"Transcription failed: {e}"}
    finally:
        if tmp_audio:
            Path(tmp_audio).unlink(missing_ok=True)

    # Build SRT content
    srt_lines = []
    for i, seg in enumerate(result.get("segments", []), 1):
        start = _format_srt_time(seg["start"])
        end = _format_srt_time(seg["end"])
        text = seg["text"].strip()
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")

    srt_content = "\n".join(srt_lines)
    Path(output).write_text(srt_content, encoding="utf-8")

    return {
        "input": str(p),
        "output": output,
        "language": result.get("language", "unknown"),
        "model": model,
        "segment_count": len(result.get("segments", [])),
        "success": True,
    }


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class TranscribePlugin(TransformerPlugin):
    """Plugin providing audio and video transcription via Whisper."""

    def __init__(self):
        super().__init__("transcribe")

    @property
    def transformers(self) -> Dict[str, callable]:
        return {}

    @property
    def skills(self) -> Dict[str, Any]:
        return {
            "audio_to_text": audio_to_text.__skill__,
            "video_to_text": video_to_text.__skill__,
            "video_to_subtitles": video_to_subtitles.__skill__,
        }

    @property
    def manifest(self):
        from ...manifest import PluginManifest, PluginRequirements
        return PluginManifest(
            name="transcribe",
            display_name="Transcription",
            description="Transcribe audio and video files to text and subtitles using Whisper.",
            icon="mic",
            group="Media",
            requires=PluginRequirements(
                filesystem=True,
                imports=["whisper"],
            ),
        )
