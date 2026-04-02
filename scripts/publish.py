"""
Publish script — the main pipeline orchestrator.
1. Reads the latest digest text
2. Converts to audio via Edge TTS
3. Adds episode to RSS feed
4. Pushes everything to GitHub (MP3 + updated feed.xml)

Can be run locally or by GitHub Actions.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(__file__))

from tts import synthesize_speech_sync
from rss import add_episode, generate_feed


def publish(digest_text: str, title: str = None, push_to_github: bool = True):
    """
    Full pipeline: text → audio → RSS → GitHub.

    Args:
        digest_text: The morning digest content
        title: Optional episode title
        push_to_github: Whether to push to GitHub (False for local testing)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    project_root = Path(__file__).parent.parent
    episodes_dir = project_root / "episodes"
    episodes_dir.mkdir(exist_ok=True)

    mp3_path = str(episodes_dir / f"{today}.mp3")
    episodes_json = str(episodes_dir / "episodes.json")
    feed_path = str(project_root / "feed.xml")

    # Step 1: Convert text to audio
    print(f"\n{'='*50}")
    print("STEP 1: Converting digest to audio...")
    print(f"{'='*50}")
    synthesize_speech_sync(digest_text, mp3_path)

    # Step 2: Add episode to feed
    print(f"\n{'='*50}")
    print("STEP 2: Adding episode to RSS feed...")
    print(f"{'='*50}")
    episode = add_episode(mp3_path, title, episodes_file=episodes_json)
    generate_feed(episodes_file=episodes_json, output_path=feed_path)
    print(f"Episode: {episode['title']}")
    print(f"Duration: {episode['duration']}")

    # Step 3: Push to GitHub
    if push_to_github:
        print(f"\n{'='*50}")
        print("STEP 3: Pushing to GitHub...")
        print(f"{'='*50}")
        push_files_to_github(
            files=[mp3_path, feed_path, episodes_json],
            commit_message=f"Add episode: {today}",
        )
    else:
        print(f"\n{'='*50}")
        print("STEP 3: Skipping GitHub push (local mode)")
        print(f"{'='*50}")

    print(f"\nDone! Episode published: {episode['title']}")
    return episode


def push_files_to_github(files: list[str], commit_message: str):
    """Push files to the GitHub repo using the GitHub API."""
    from github import Github
    import base64

    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")

    if not token or not repo_name:
        print("WARNING: GITHUB_TOKEN or GITHUB_REPO not set. Skipping push.")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)
    project_root = str(Path(__file__).parent.parent)

    for file_path in files:
        rel_path = os.path.relpath(file_path, project_root)
        print(f"  Uploading {rel_path}...")

        with open(file_path, "rb") as f:
            content = f.read()

        try:
            existing = repo.get_contents(rel_path)
            repo.update_file(rel_path, commit_message, content, existing.sha)
        except Exception:
            repo.create_file(rel_path, commit_message, content)

    print("  All files pushed to GitHub.")


# --- CLI entry point ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python publish.py <digest_text_file> [--local]")
        print("")
        print("Options:")
        print("  --local    Skip pushing to GitHub (for testing)")
        print("")
        print("Example:")
        print("  python publish.py ../digest.txt")
        print("  python publish.py ../digest.txt --local")
        sys.exit(1)

    input_file = sys.argv[1]
    local_mode = "--local" in sys.argv

    with open(input_file, "r") as f:
        digest_text = f.read()

    publish(digest_text, push_to_github=not local_mode)
