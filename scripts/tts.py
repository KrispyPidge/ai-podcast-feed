"""
Text-to-Speech converter using xAI Grok TTS API.

The podcast script is pre-processed by `preprocess_for_grok()` below, then
POSTed to the xAI TTS endpoint. The preprocessor fixes three things we've
seen Grok mishandle:

  1. `[pause 500ms]` duration-style tokens - spoken aloud literally.
     Converted to `[pause]` (<500ms) or `[long-pause]` (>=500ms).
  2. Unsupported wrap tags like `<emphasis>...</emphasis>` - also spoken
     aloud. Stripped (inner text preserved).
  3. Optional: inject `[breath]` at blank-line paragraph breaks for
     more natural pacing (on by default).

Supported Grok TTS tags (verified April 2026 against docs.x.ai):
  Inline (self-closing):
    [pause]  [long-pause]  [laugh]  [cry]  [breath]  [sigh]
    [chuckle]  [giggle]  [smirk]  [throat-clear]  [inhale]  [exhale]
    [tsk]  [tongue-click]  [lip-smack]  [hum-tune]
  Wrapping (open/close):
    <whisper>  <singing>  <sing-song>  <laugh-speak>
    <soft>  <loud>  <slow>  <fast>
    <build-intensity>  <decrease-intensity>
    <higher-pitch>  <lower-pitch>

Voices: ara, eve, leo, rex, sal
Docs:   https://docs.x.ai/developers/model-capabilities/audio/text-to-speech
"""

import os
import re
import sys
from datetime import datetime

import requests


XAI_TTS_ENDPOINT = "https://api.x.ai/v1/tts"
DEFAULT_VOICE = os.getenv("XAI_VOICE", "eve")
DEFAULT_LANGUAGE = "en"

# Wrapping tags Grok TTS actually parses. Everything else is stripped
# by preprocess_for_grok so the text isn't read out with the tag name.
_SUPPORTED_WRAP_TAGS = {
    "whisper", "singing", "sing-song", "laugh-speak",
    "soft", "loud", "slow", "fast",
    "build-intensity", "decrease-intensity",
    "higher-pitch", "lower-pitch",
}


def preprocess_for_grok(text: str, add_paragraph_breaths: bool = True) -> str:
    """
    Normalise a digest script so Grok TTS renders tags correctly.

    Args:
        text: Raw script, possibly with legacy `[pause 500ms]` or
              `<emphasis>...</emphasis>` syntax.
        add_paragraph_breaths: If True (default), inject `[breath]` at every
              blank-line paragraph break. Set False if Eve sounds asthmatic.

    Returns:
        Cleaned text safe to send to the xAI TTS endpoint.
    """
    # 1a. [pause 500ms] -> [pause] or [long-pause]
    def _norm_ms(match: re.Match) -> str:
        try:
            ms = float(match.group(1))
        except (TypeError, ValueError):
            return "[pause]"
        return "[long-pause]" if ms >= 500 else "[pause]"

    text = re.sub(
        r"\[pause[\s:]*([0-9]*\.?[0-9]+)\s*ms\]",
        _norm_ms,
        text,
        flags=re.IGNORECASE,
    )

    # 1b. [pause Xs] seconds form -> [pause] or [long-pause]
    text = re.sub(
        r"\[pause[\s:]*([0-9]*\.?[0-9]+)\s*s\]",
        lambda m: "[long-pause]" if float(m.group(1)) >= 0.5 else "[pause]",
        text,
        flags=re.IGNORECASE,
    )

    # 2. Strip wrap tags Grok doesn't recognise (keep the inner text).
    #    <emphasis>Canva</emphasis> -> Canva
    def _filter_wrap(match: re.Match) -> str:
        tag = match.group(1).lower().lstrip("/")
        return match.group(0) if tag in _SUPPORTED_WRAP_TAGS else ""

    text = re.sub(r"</?([a-zA-Z-]+)>", _filter_wrap, text)

    # 3. Breath on every blank-line paragraph break
    if add_paragraph_breaths:
        text = re.sub(r"\n[ \t]*\n", "\n[breath]\n\n", text)

    return text


def synthesize_speech_sync(
    text: str,
    output_path: str,
    voice: str | None = None,
    rate: str | None = None,   # unused; kept for compatibility with old signature
    pitch: str | None = None,  # unused; kept for compatibility with old signature
) -> str:
    """
    Convert text to speech using xAI Grok TTS API and save as MP3.

    Args:
        text:        Podcast script (may include Grok TTS tags)
        output_path: Where to save the MP3
        voice:       xAI voice id (ara, eve, leo, rex, sal). Defaults to $XAI_VOICE or "eve".

    Returns:
        Path to the generated MP3 file.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "XAI_API_KEY environment variable is not set. "
            "Add it as a repo secret: Settings -> Secrets and variables -> Actions."
        )

    voice = voice or DEFAULT_VOICE

    # Clean the script for Grok's actual tag vocabulary before sending
    cleaned_text = preprocess_for_grok(text)

    response = requests.post(
        XAI_TTS_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "text": cleaned_text,
            "voice_id": voice,
            "language": DEFAULT_LANGUAGE,
        },
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"xAI TTS API failed (status {response.status_code}): {response.text[:500]}"
        )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Audio saved to {output_path} (voice: {voice}, {len(response.content):,} bytes)")
    return output_path


# --- CLI entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts.py <input_text_file> [output_mp3_path] [voice]")
        print()
        print("Voices: ara, eve, leo, rex, sal")
        print()
        print("Examples:")
        print("  python tts.py digest.txt")
        print("  python tts.py digest.txt episodes/2026-04-18.mp3 eve")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        digest_text = f.read()

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = f"episodes/{today}.mp3"

    voice = sys.argv[3] if len(sys.argv) >= 4 else DEFAULT_VOICE

    synthesize_speech_sync(digest_text, output_file, voice)
