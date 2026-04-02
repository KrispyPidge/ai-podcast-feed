"""
Google Cloud TTS version — swap this in later if you want
more voice control, SSML support, or Studio-quality voices.

Requires:
  - Google Cloud account with TTS API enabled
  - Service account key (JSON)
  - Set GOOGLE_APPLICATION_CREDENTIALS env var to the key path

Setup guide: https://cloud.google.com/text-to-speech/docs/before-you-begin
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def synthesize_speech(text: str, output_path: str, voice_name: str = "en-US-Studio-O") -> str:
    """
    Convert text to speech using Google Cloud TTS.

    Voices:
        en-US-Studio-O  — natural male (free tier)
        en-US-Studio-Q  — natural female (free tier)
        en-US-Neural2-D — male, very clear
    Full list: https://cloud.google.com/text-to-speech/docs/voices
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    max_bytes = 4800
    chunks = _chunk_text(text, max_bytes)

    if len(chunks) == 1:
        audio_content = _synthesize_chunk(client, chunks[0], voice_name)
    else:
        from pydub import AudioSegment
        import io

        combined = AudioSegment.empty()
        for i, chunk in enumerate(chunks):
            print(f"  Synthesizing chunk {i + 1}/{len(chunks)}...")
            chunk_audio = _synthesize_chunk(client, chunk, voice_name)
            segment = AudioSegment.from_mp3(io.BytesIO(chunk_audio))
            combined += segment

        combined.export(output_path, format="mp3", bitrate="128k")
        print(f"Audio saved to {output_path}")
        return output_path

    with open(output_path, "wb") as f:
        f.write(audio_content)

    print(f"Audio saved to {output_path}")
    return output_path


def _synthesize_chunk(client, text: str, voice_name: str) -> bytes:
    from google.cloud import texttospeech

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name=voice_name,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0,
        effects_profile_id=["headphone-class-device"],
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content


def _chunk_text(text: str, max_bytes: int) -> list[str]:
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        test = current_chunk + "\n\n" + para if current_chunk else para
        if len(test.encode("utf-8")) <= max_bytes:
            current_chunk = test
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para.encode("utf-8")) > max_bytes:
                sentences = para.replace(". ", ".\n").split("\n")
                for sentence in sentences:
                    if current_chunk and len((current_chunk + " " + sentence).encode("utf-8")) <= max_bytes:
                        current_chunk += " " + sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts_google.py <input_text_file> [output_mp3_path]")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        digest_text = f.read()

    output_file = sys.argv[2] if len(sys.argv) >= 3 else f"episodes/{datetime.now().strftime('%Y-%m-%d')}.mp3"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    synthesize_speech(digest_text, output_file)
