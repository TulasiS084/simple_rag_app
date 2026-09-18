import io
import base64
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def clean_text_for_speech(text: str) -> str:
    """Strip markdown formatting, emojis, and urls to make speech natural and clear."""
    # Remove code blocks
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove markdown headers, bold, italics, blockquotes, bullets
    cleaned = re.sub(r'[*#_>`\[\]]', ' ', cleaned)
    # Remove URLs
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Remove common emojis so TTS doesn't say emoji names
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def text_to_speech_base64(text: str, lang: str = "en") -> Optional[str]:
    """
    Converts text to MP3 audio base64 data URI using gTTS if available.
    Returns base64 audio data URI: 'data:audio/mp3;base64,...' or None.
    """
    cleaned = clean_text_for_speech(text)
    if not cleaned:
        return None

    try:
        from gtts import gTTS
        fp = io.BytesIO()
        # Limit speech to first 1000 chars for instant responsiveness
        speech_text = cleaned[:1000]
        tts = gTTS(text=speech_text, lang=lang, slow=False)
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_b64 = base64.b64encode(fp.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{audio_b64}"
    except Exception as e:
        logger.debug(f"gTTS not available or offline: {e}")
        return None
