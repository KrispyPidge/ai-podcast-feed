"""
Text-to-Speech converter using xAI Grok TTS API.

The podcast script is expected to be pre-formatted for speech with
Grok TTS tags (e.g. [pause 500ms], <emphasis>word</emphasis>, <slow>...</slow>,
<whisper>...</whisper>, [laugh]).

Voices: ara, eve, leo, rex, sal
Docs: https://docs.x.ai/developers/model-capabilities/audio/text-to-speech
"""

import os
import sys
from datetime import datetime

import requests


XAI_TTS_ENDPOINT = "https://api.x.ai/v1/tts"
DEFAULT_VOICE = os.getenv("XAI_VOICE", "eve")
DEFAULT_LANGUAGE = "en"


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

    response = requests.post(
        XAI_TTS_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
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
