"""
RSS feed generator for the podcast.
Reads existing feed, appends a new episode, writes updated XML.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from email.utils import format_datetime
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

# --- RSS feed template ---
FEED_TEMPLATE = Template("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{{ podcast_title }}</title>
    <link>{{ podcast_link }}</link>
    <description>{{ podcast_description }}</description>
    <language>en-us</language>
    <itunes:author>{{ podcast_author }}</itunes:author>
    <itunes:image href="{{ podcast_image_url }}"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Technology"/>
    <atom:link href="{{ feed_url }}" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{{ last_build_date }}</lastBuildDate>
    {% for episode in episodes %}
    <item>
      <title>{{ episode.title }}</title>
      <description>{{ episode.description }}</description>
      <enclosure url="{{ episode.audio_url }}" length="{{ episode.file_size }}" type="audio/mpeg"/>
      <guid isPermaLink="true">{{ episode.audio_url }}</guid>
      <pubDate>{{ episode.pub_date }}</pubDate>
      <itunes:duration>{{ episode.duration }}</itunes:duration>
      <itunes:episode>{{ episode.number }}</itunes:episode>
    </item>
    {% endfor %}
  </channel>
</rss>""")


def load_episodes(episodes_file: str) -> list[dict]:
    """Load episode metadata from a JSON file."""
    import json
    if os.path.exists(episodes_file):
        with open(episodes_file, "r") as f:
            return json.load(f)
    return []


def save_episodes(episodes: list[dict], episodes_file: str):
    """Save episode metadata to a JSON file."""
    import json
    with open(episodes_file, "w") as f:
        json.dump(episodes, f, indent=2)


def get_audio_duration(mp3_path: str) -> str:
    """Get duration of an MP3 file as HH:MM:SS."""
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(mp3_path)
    total_seconds = int(len(audio) / 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def add_episode(
    mp3_path: str,
    title: str = None,
    description: str = "Your daily AI-generated audio digest.",
    episodes_file: str = "episodes/episodes.json",
) -> dict:
    """
    Add a new episode to the feed.

    Args:
        mp3_path: Path to the MP3 file
        title: Episode title (defaults to date-based)
        description: Episode description
        episodes_file: Path to the episodes metadata JSON

    Returns:
        The new episode dict
    """
    episodes = load_episodes(episodes_file)

    today = datetime.now().strftime("%Y-%m-%d")
    if title is None:
        title = f"Daily Digest — {datetime.now().strftime('%A, %B %d, %Y')}"

    base_url = os.getenv("PODCAST_LINK", "").rstrip("/")
    mp3_filename = os.path.basename(mp3_path)
    audio_url = f"{base_url}/episodes/{mp3_filename}"
    file_size = os.path.getsize(mp3_path)
    duration = get_audio_duration(mp3_path)

    episode = {
        "title": title,
        "description": description,
        "audio_url": audio_url,
        "file_size": file_size,
        "duration": duration,
        "pub_date": format_datetime(datetime.now(timezone.utc)),
        "number": len(episodes) + 1,
        "date": today,
    }

    episodes.insert(0, episode)  # newest first
    save_episodes(episodes, episodes_file)

    return episode


def generate_feed(episodes_file: str = "episodes/episodes.json", output_path: str = "feed.xml"):
    """Generate the RSS XML feed from episode metadata."""
    episodes = load_episodes(episodes_file)

    feed_xml = FEED_TEMPLATE.render(
        podcast_title=os.getenv("PODCAST_TITLE", "AI Morning Digest"),
        podcast_link=os.getenv("PODCAST_LINK", ""),
        podcast_description=os.getenv("PODCAST_DESCRIPTION", "A daily AI-generated audio digest."),
        podcast_author=os.getenv("PODCAST_AUTHOR", "Chris"),
        podcast_image_url=os.getenv("PODCAST_IMAGE_URL", ""),
        feed_url=f"{os.getenv('PODCAST_LINK', '').rstrip('/')}/feed.xml",
        last_build_date=format_datetime(datetime.now(timezone.utc)),
        episodes=episodes,
    )

    with open(output_path, "w") as f:
        f.write(feed_xml)

    print(f"RSS feed written to {output_path} ({len(episodes)} episodes)")
    return output_path


# --- CLI entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rss.py add <mp3_path> [title]    — Add episode and regenerate feed")
        print("  python rss.py generate                   — Regenerate feed from existing episodes")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        mp3_path = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) >= 4 else None
        episode = add_episode(mp3_path, title)
        print(f"Added episode: {episode['title']}")
        generate_feed()

    elif command == "generate":
        generate_feed()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
