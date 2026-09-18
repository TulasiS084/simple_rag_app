import io
import base64
import re
import os
import sys
import subprocess
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def clean_text_for_speech(text: str) -> str:
    """Strip markdown formatting, emojis, and urls to make speech natural, clean, and clear."""
    # Remove code blocks
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove markdown headers, bold, italics, blockquotes, bullets
    cleaned = re.sub(r'[*#_>`\[\]\(\)]', ' ', cleaned)
    # Remove URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Remove common emojis
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def generate_speech_audio(text: str, volume: int = 100, rate: int = 0) -> Optional[bytes]:
    """
    Generates loud, clear spoken audio bytes (WAV or MP3).
    Tries:
    1. Built-in Windows SAPI SpeechSynthesizer (offline, loud, instant on Windows)
    2. gTTS (Google Text-to-Speech MP3)
    3. pyttsx3
    """
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        return None

    # Truncate to reasonable speech length for fast generation
    speech_text = cleaned[:1200]

    # 1. On Windows, use built-in System.Speech.Synthesis (100% offline, zero install, loud)
    if sys.platform == "win32":
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_wav = tmp_file.name

            # Escape single quotes for PowerShell
            safe_text = speech_text.replace("'", "''").replace('"', '`"')
            
            ps_script = (
                f"Add-Type -AssemblyName System.Speech; "
                f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.Volume = {min(max(volume, 0), 100)}; "
                f"$synth.Rate = {min(max(rate, -10), 10)}; "
                f"$synth.SetOutputToWaveFile('{tmp_wav}'); "
                f"$synth.Speak('{safe_text}'); "
                f"$synth.Dispose();"
            )
            
            # Execute powershell in background
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=12
            )
            
            if os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 1000:
                with open(tmp_wav, "rb") as f:
                    audio_bytes = f.read()
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
                return audio_bytes
        except Exception as e:
            logger.debug(f"Windows SpeechSynthesizer error: {e}")

    # 2. Fallback to gTTS if installed
    try:
        from gtts import gTTS
        fp = io.BytesIO()
        tts = gTTS(text=speech_text, lang="en", slow=False)
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        logger.debug(f"gTTS fallback error: {e}")

    # 3. Fallback to pyttsx3 if installed
    try:
        import pyttsx3
        engine = pyttsx3.init()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_wav = tmp_file.name
        engine.save_to_file(speech_text, tmp_wav)
        engine.runAndWait()
        if os.path.exists(tmp_wav):
            with open(tmp_wav, "rb") as f:
                data = f.read()
            os.remove(tmp_wav)
            return data
    except Exception as e:
        logger.debug(f"pyttsx3 fallback error: {e}")

    return None


def text_to_speech_base64(text: str) -> Optional[str]:
    """Returns base64 data URI for audio or None."""
    audio_data = generate_speech_audio(text)
    if audio_data:
        b64 = base64.b64encode(audio_data).decode("utf-8")
        return f"data:audio/wav;base64,{b64}"
    return None
