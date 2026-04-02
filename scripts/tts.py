"""
Text-to-Speech converter using Microsoft Edge TTS.
Zero config, zero cost, natural-sounding voices.

To swap to Google Cloud TTS later, see tts_google.py.
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Optional: prep_text can pre-process raw digest text for TTS.
# Not needed when the input is already a podcast script (from the scheduled task).
try:
    from prep_text import prep_for_speech
except ImportError:
    prep_for_speech = None


# Edge TTS voices worth trying (all free, all natural-sounding):
#   en-GB-RyanNeural      — British male, warm and clear (great for news)
#   en-GB-SoniaNeural     — British female, professional
#   en-US-GuyNeural       — American male, conversational
#   en-US-JennyNeural     — American female, friendly
#   en-US-AriaNeural      — American female, expressive
#   en-AU-WilliamNeural   — Australian male
#
# Full list: run `edge-tts --list-voices`

DEFAULT_VOICE = "en-GB-RyanNeural"
DEFAULT_RATE = "-5%"  # Slightly slower than normal — gives acronyms room to breathe


async def synthesize_speech(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = "+0Hz",
) -> str:
    """
    Convert text to speech using Edge TTS.

    Args:
        text:        The digest text to convert
        output_path: Where to save the MP3
        voice:       Edge TTS voice name
        rate:        Speed adjustment (e.g. "+10%", "-5%")
        pitch:       Pitch adjustment (e.g. "+5Hz", "-2Hz")

    Returns:
        Path to the generated MP3 file
    """
    import edge_tts

    # Preprocess text if prep_text is available (not needed for pre-written podcast scripts)
    if prep_for_speech is not None:
        text = prep_for_speech(text)

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)
    print(f"Audio saved to {output_path}")
    return output_path


def synthesize_speech_sync(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = "+0Hz",
) -> str:
    """Synchronous wrapper around synthesize_speech."""
    return asyncio.run(synthesize_speech(text, output_path, voice, rate, pitch))


# --- CLI entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts.py <input_text_file> [output_mp3_path] [voice]")
        print()
        print("Examples:")
        print("  python tts.py digest.txt")
        print("  python tts.py digest.txt episodes/2026-04-02.mp3")
        print("  python tts.py digest.txt episodes/2026-04-02.mp3 en-US-GuyNeural")
        print()
        print("Popular voices:")
        print("  en-GB-RyanNeural    — British male (default)")
        print("  en-GB-SoniaNeural   — British female")
        print("  en-US-GuyNeural     — American male")
        print("  en-US-JennyNeural   — American female")
        print()
        print("Full voice list: edge-tts --list-voices")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        digest_text = f.read()

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_file = f"episodes/{today}.mp3"

    voice = sys.argv[3] if len(sys.argv) >= 4 else DEFAULT_VOICE

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    synthesize_speech_sync(digest_text, output_file, voice)
