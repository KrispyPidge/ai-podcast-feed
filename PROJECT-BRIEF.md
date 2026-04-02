# AI Podcast Feed — Project Brief

## What This Is
An automated pipeline that converts Chris's daily AI news digest into a podcast episode and publishes it to a private RSS feed on GitHub Pages. Friends subscribe in any podcast app (Pocket Casts, Overcast, Apple Podcasts) and get new episodes automatically.

## Current State (as of 2 April 2026)

### What's Done
- **Full project scaffold** built and sitting in this folder
- **Edge TTS** chosen over Google Cloud TTS — zero accounts, zero API keys, zero cost
- **Text-to-speech works locally** — tested with today's digest, sounds good
- **Podcast script format figured out** — the digest needs to be rewritten for speech, not just fed raw into TTS. Key rules:
  - All numbers written as words ("three point one" not "3.1")
  - Acronyms with periods between letters ("A.I.", "G.P.T.", "L.L.M.")
  - Commas after the word "four" (Edge TTS clips it otherwise)
  - Em dashes replaced with commas
  - No URLs, emoji, or markdown formatting
  - Natural spoken transitions between sections
  - Opening greeting and closing sign-off
- **Morning digest scheduled task updated** — now creates TWO Gmail drafts every morning at 6 AM:
  1. `☀️ Your Daily AI Digest` — the original email version for reading/sharing
  2. `🎙️ Podcast Script` — the spoken version with all TTS rules baked in
- **Speaking rate** set to -5% for clearer delivery

### What's Left to Do
1. **Create GitHub repo** — new public repo called `ai-podcast-feed`, push this scaffold to it
2. **Enable GitHub Pages** — Settings → Pages → Deploy from branch → main / root
3. **Wire up the pipeline** — the podcast script Gmail draft needs to flow into the TTS + RSS pipeline automatically. Options:
   - GitHub Actions workflow (already scaffolded at `.github/workflows/publish-episode.yml`) runs on a cron, but needs a way to pull the podcast script text from Gmail
   - Or: create a second scheduled task that reads the podcast script draft from Gmail, runs TTS locally or triggers the GitHub Action
4. **Test the RSS feed** — subscribe in Pocket Casts using the GitHub Pages feed URL
5. **Verify end-to-end** — confirm the full loop: digest task → podcast script draft → TTS → MP3 → RSS → podcast app

### Stretch Goals (not started)
- Custom podcast cover art
- Intro/outro music clip
- Different voices for different sections
- Episode show notes in the RSS description
- Cleanup script for old episodes (GitHub has a soft 1GB repo limit)

## Project Structure
```
ai-podcast-feed/
├── .github/workflows/
│   └── publish-episode.yml     # GitHub Actions daily automation
├── scripts/
│   ├── tts.py                  # Edge TTS (default, zero config)
│   ├── tts_google.py           # Google Cloud TTS (optional upgrade)
│   ├── prep_text.py            # Text preprocessor (legacy, not needed if using podcast script from scheduled task)
│   ├── rss.py                  # RSS feed generation
│   └── publish.py              # Pipeline orchestrator: text → audio → RSS → GitHub
├── episodes/                   # Generated MP3s + metadata
├── assets/                     # Cover art
├── feed.xml                    # Starter RSS feed (served by GitHub Pages)
├── digest.txt                  # Today's podcast script (used for local testing)
├── requirements.txt            # edge-tts, pydub, PyGithub, python-dotenv, Jinja2
├── .env.example                # Template for environment variables
├── .gitignore
└── README.md                   # Full setup and build guide
```

## Key Technical Decisions
- **Edge TTS over Google Cloud TTS** — no account setup, no API key, no cost. Voice: `en-GB-RyanNeural` (British male). Can swap to Google Cloud later using `tts_google.py`.
- **LLM rewrite over regex preprocessing** — instead of using `prep_text.py` to regex-transform the email digest, the scheduled task now produces a purpose-built podcast script. Much more natural results.
- **GitHub Pages for hosting** — free, serves both MP3 files and RSS XML. Soft limits (1GB storage, 100GB/month bandwidth) are irrelevant for this use case.
- **Pocket Casts as primary app** — Chris uses Pocket Casts. Feed URL works in any podcast app that supports custom RSS.

## How to Test Locally Right Now
```
cd "C:\Users\djbla\OneDrive\Documents\Claude\Projects\Vibe Coding Chris Brain\ai-podcast-feed"
venv\Scripts\activate
python scripts/tts.py digest.txt episodes/test.mp3
start episodes\test.mp3
```

## Chris's Setup
- Windows PC (C:\Users\djbla)
- Project folder: `C:\Users\djbla\OneDrive\Documents\Claude\Projects\Vibe Coding Chris Brain\ai-podcast-feed`
- Python venv already created and working
- Pocket Casts installed
- No Google Cloud account (not needed with Edge TTS)
- GitHub account exists (integration set up in Claude)
