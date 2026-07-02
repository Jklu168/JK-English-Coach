# JK English Coach

JK English Coach is a personal AI-assisted English vocabulary learning system.

It combines:

- Spaced Repetition
- SQLite progress tracking
- Audio Cache
- AI-assisted development

to help users build a sustainable daily English learning habit.

**Learn smarter. Improve every day.**

## Features

- Review Today mode
- New Words mode
- Random by Difficulty mode
- Again / Good / Easy spaced repetition
- SQLite learning progress
- Daily learning statistics
- Audio cache playback
- Dashboard
- Keyboard shortcuts

## Project History

This project was originally developed as Ed5k, an English 5000-word learning tool created by JK.
Starting from v5.0.0, it is officially renamed to JK English Coach.

## Run

```bash
pip install -r requirements.txt
python src/main.py
```

## Audio Cache

JK English Coach uses local Piper WAV audio cache by default.
Existing MP3 cache files are still supported.
gTTS is kept only as fallback because bulk generation may hit HTTP 429 rate limits.

To generate audio files:

```bash
python tools/generate_audio.py
```

To verify audio cache:

```bash
python tools/verify_audio_cache.py
```

## Folder Notes

Archive contains historical scripts, prompts, databases, and releases for reference only.
