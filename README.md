# AI Podcast Feed

A personal, automated podcast pipeline that converts your morning AI digest into audio and publishes it to a private RSS feed your friends can subscribe to in any podcast app.

## How It Works

```
Morning Digest (text) → Edge TTS (audio) → RSS Feed (XML) → GitHub Pages → Podcast Apps
```

## Quick Start — Hear Your First Episode

This takes about 2 minutes. No accounts to set up, no API keys.

```bash
# 1. Open a terminal in this folder, set up Python
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Generate audio from today's digest
python scripts/tts.py digest.txt episodes/test.mp3

# 3. Play it!
# macOS: open episodes/test.mp3
# Windows: start episodes/test.mp3
# Linux: xdg-open episodes/test.mp3
```

That's it. You should hear your digest read aloud by a natural British voice.

### Try Different Voices

```bash
python scripts/tts.py digest.txt episodes/test.mp3 en-US-GuyNeural       # American male
python scripts/tts.py digest.txt episodes/test.mp3 en-GB-SoniaNeural     # British female
python scripts/tts.py digest.txt episodes/test.mp3 en-US-AriaNeural      # American female

# See all available voices:
edge-tts --list-voices
```


## Set Up the RSS Feed (GitHub Pages)

### 1. Create a GitHub repo

- Create a new public repo called `ai-podcast-feed`
- Push this folder to it:

```bash
git init
git add .
git commit -m "Initial podcast setup"
git remote add origin https://github.com/YOUR-USERNAME/ai-podcast-feed.git
git push -u origin main
```

### 2. Enable GitHub Pages

- Repo → Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder: `/ (root)` → Save
- Wait ~1 minute, then visit: `https://YOUR-USERNAME.github.io/ai-podcast-feed/feed.xml`

### 3. Update your config

```bash
cp .env.example .env
# Edit .env — update PODCAST_LINK with your actual GitHub Pages URL
#   e.g. https://YOUR-USERNAME.github.io/ai-podcast-feed/
```

### 4. Test the full pipeline

```bash
python scripts/publish.py digest.txt --local

# Check that these were created:
#   episodes/YYYY-MM-DD.mp3
#   episodes/episodes.json
#   feed.xml (updated with the new episode)
```

### 5. Push and subscribe

```bash
git add .
git commit -m "First episode"
git push
```

Subscribe in your podcast app:
- **Pocket Casts**: Search → "Add by URL" → paste your feed.xml URL
- **Overcast**: Add URL → paste feed URL
- **Apple Podcasts**: Library → ··· → Add Show by URL
- **Spotify**: Not supported for custom RSS (use Pocket Casts or Overcast)


## Automation (GitHub Actions)

The workflow at `.github/workflows/publish-episode.yml` runs daily on a cron schedule. To activate it:

1. Commit a `latest-digest.txt` file to the repo (your digest pipeline writes this)
2. OR trigger manually: Actions → Publish Episode → Run workflow → paste digest text

No secrets or API keys needed — Edge TTS runs entirely without authentication.


## Stretch Goals

- [ ] Custom cover art (DALL-E or Ideogram free tier → `assets/cover.jpg`)
- [ ] Intro/outro music clip
- [ ] Section voices (different Edge TTS voice per section)
- [ ] Episode show notes (HTML in RSS description)
- [ ] Upgrade to Google Cloud TTS for Studio voices (`tts_google.py` included)


## Project Structure

```
ai-podcast-feed/
├── .github/workflows/
│   └── publish-episode.yml     # Daily automation
├── scripts/
│   ├── tts.py                  # Edge TTS (default, zero config)
│   ├── tts_google.py           # Google Cloud TTS (optional upgrade)
│   ├── rss.py                  # RSS feed generation
│   └── publish.py              # Pipeline orchestrator
├── episodes/                   # Generated MP3s + metadata
├── assets/                     # Cover art
├── feed.xml                    # RSS feed (served by GitHub Pages)
├── digest.txt                  # Sample digest for testing
├── requirements.txt
├── .env.example
└── .gitignore
```
