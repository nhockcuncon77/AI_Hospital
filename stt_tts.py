"""
Speech-to-Text (Whisper) and Text-to-Speech (OpenAI TTS) with Twilio-compatible output.
"""
import io
import logging
from typing import Optional

from openai import OpenAI

from audio_utils import pcm_24k_to_mulaw_8k, mulaw_buffer_to_wav_io
from config import OPENAI_API_KEY, OPENAI_API_BASE

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _client_or_default() -> OpenAI:
    global _client
    if _client is None:
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_API_BASE:
            kwargs["base_url"] = OPENAI_API_BASE
        _client = OpenAI(**kwargs)
    return _client


def transcribe_mulaw(mulaw_bytes: bytes) -> str:
    """
    Transcribe 8kHz mulaw audio (from Twilio) to text using Whisper.
    Returns empty string if audio is too short or silent.
    """
    if len(mulaw_bytes) < 800:  # < ~50ms
        return ""
    try:
        wav_io = mulaw_buffer_to_wav_io(mulaw_bytes)
        client = _client_or_default()
        wav_io.name = "audio.wav"
        r = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_io,
        )
        text = (r.text or "").strip()
        return text
    except Exception as e:
        logger.warning("Transcribe failed: %s", e)
        return ""


def text_to_mulaw(
    text: str,
    voice: str = "nova",
    model: str = "tts-1",
) -> bytes:
    """
    Convert text to 8kHz mulaw for Twilio using OpenAI TTS.
    Uses PCM internally then converts to mulaw 8k.
    """
    if not text.strip():
        return b""
    client = _client_or_default()
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="pcm",
        speed=1.0,
    )
    pcm_24k = response.content
    return pcm_24k_to_mulaw_8k(pcm_24k)
