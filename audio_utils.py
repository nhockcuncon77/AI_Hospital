"""
Audio conversion for Twilio (8kHz mulaw) and OpenAI (Whisper / TTS).
Twilio Media Streams: inbound/outbound audio is audio/x-mulaw, 8000 Hz, mono.
Uses pure Python + numpy (no audioop; audioop was removed in Python 3.13).
"""
import base64
import io
import struct
import wave

import numpy as np

# Twilio format
SAMPLE_RATE_TWILIO = 8000
# OpenAI TTS default
SAMPLE_RATE_TTS = 24000

# G.711 mu-law decode table (8-bit -> 16-bit linear)
_ULAW_EXPAND_TABLE = None


def _ulaw_expand_table():
    global _ULAW_EXPAND_TABLE
    if _ULAW_EXPAND_TABLE is not None:
        return _ULAW_EXPAND_TABLE
    table = []
    for u in range(256):
        u = u ^ 0xFF
        sign = (u & 0x80) and -1 or 1
        exponent = (u >> 4) & 0x07
        mantissa = u & 0x0F
        sample = sign * ((((mantissa << 3) + 0x84) << exponent) - 0x84)
        table.append(max(-32768, min(32767, sample)))
    _ULAW_EXPAND_TABLE = table
    return table


def mulaw_to_pcm(mulaw_bytes: bytes) -> bytes:
    """Convert 8-bit mulaw to 16-bit linear PCM (for Whisper)."""
    table = _ulaw_expand_table()
    pcm = bytearray(len(mulaw_bytes) * 2)
    for i, u in enumerate(mulaw_bytes):
        s = table[u]
        struct.pack_into("<h", pcm, i * 2, s)
    return bytes(pcm)


def _linear_to_ulaw(sample: int) -> int:
    """16-bit linear -> 8-bit mu-law (ITU-T G.711)."""
    if sample < 0:
        sign = 0x80
        sample = -sample
    else:
        sign = 0
    sample = min(sample, 32635)
    sample += 0x21  # BIAS
    exp_mask = 0x4000
    exponent = 7
    while exponent > 0 and sample <= exp_mask:
        exp_mask >>= 1
        exponent -= 1
    mantissa = (sample >> (exponent + 3)) & 0x0F
    return (0xFF ^ (sign | (exponent << 4) | mantissa)) & 0xFF


def pcm_16_to_mulaw(pcm_16_bytes: bytes, sample_rate: int = SAMPLE_RATE_TTS) -> bytes:
    """Convert 16-bit PCM at given sample rate to 8kHz mulaw for Twilio."""
    arr = np.frombuffer(pcm_16_bytes, dtype=np.int16)
    if sample_rate != SAMPLE_RATE_TWILIO:
        n_out = int(len(arr) * SAMPLE_RATE_TWILIO / sample_rate)
        indices = np.linspace(0, len(arr) - 1, n_out, dtype=np.int64)
        arr = arr[indices]
    out = bytearray(len(arr))
    for i in range(len(arr)):
        out[i] = _linear_to_ulaw(int(arr[i]))
    return bytes(out)


def mulaw_buffer_to_wav_io(mulaw_bytes: bytes) -> io.BytesIO:
    """Convert mulaw 8kHz buffer to WAV in memory for Whisper API."""
    pcm = mulaw_to_pcm(mulaw_bytes)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE_TWILIO)
        wav.writeframes(pcm)
    buf.seek(0)
    return buf


def pcm_24k_to_mulaw_8k(pcm_24k_16bit: bytes) -> bytes:
    """Convert OpenAI TTS PCM (24kHz 16-bit) to 8kHz mulaw for Twilio."""
    return pcm_16_to_mulaw(pcm_24k_16bit, sample_rate=24000)


def mulaw_chunks_to_base64(mulaw_bytes: bytes, chunk_size: int = 320) -> list[str]:
    """Split mulaw into Twilio-sized chunks (320 bytes = 20ms at 8kHz) and base64 encode."""
    chunks = []
    for i in range(0, len(mulaw_bytes), chunk_size):
        chunk = mulaw_bytes[i : i + chunk_size]
        chunks.append(base64.b64encode(chunk).decode("ascii"))
    return chunks
