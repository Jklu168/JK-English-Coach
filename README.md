# JK English Coach

**Version:** v5.1.0  
**Release:** Foundation Release

JK English Coach is an AI-assisted English vocabulary learning system with offline Piper TTS support. It is designed as a practical desktop learning tool with local data storage, cached audio playback, and a spaced repetition workflow.

## Screenshot

![JK English Coach Main Screen](docs/main_screen_v5_1_0.png)

Main menu of JK English Coach v5.1.0 Foundation Release.

Features shown in this screen:

- Review Today mode
- New Words mode
- Random by Difficulty mode
- Learning statistics dashboard
- Audio cache status
- Session delay setting
- Session repeat setting
- Keyboard shortcut hints

## Features

- Spaced repetition learning workflow
- Offline Piper TTS support
- gTTS compatibility mode
- Review Today dashboard
- Session delay setting
- Session repeat count setting
- Keyboard shortcut support
- Mouse button interaction
- SQLite learning progress tracking
- Fully offline learning experience
- Audio cache support
- AI-assisted project development workflow

## Project Structure

```text
JK English Coach
|
+-- src/                # Main application source code
+-- tools/              # Utility scripts
+-- data/               # Vocabulary CSV and SQLite database
+-- audio_cache/        # Offline audio library
+-- models/             # Piper TTS models
+-- prompts/            # AI prompts and templates
+-- logs/               # Runtime logs
+-- backup/             # Backup files
+-- exports/            # Exported files
+-- Archive/            # Legacy versions and history
|
+-- README.md
+-- CHANGELOG.md
+-- TODO.md
+-- requirements.txt
+-- .gitignore
+-- .gitattributes
```

## Installation

```bash
git clone <repository-url>
cd "JK English Coach"
pip install -r requirements.txt
python src/main.py
```

## Dependencies

- Python 3.11+
- pygame
- sqlite3
- Piper TTS

## Audio Engine

**Primary TTS:** Offline Piper TTS  
**Compatibility:** gTTS MP3  
**Audio Library:** 4314 words

JK English Coach uses local Piper audio cache files for offline playback. Existing gTTS MP3 files remain supported for compatibility.

Utility scripts:

```bash
python tools/generate_audio.py
python tools/verify_audio_cache.py
```

## Usage

Start the application:

```bash
python src/main.py
```

The application opens a pygame window for mode selection and learning sessions. Learning progress is stored locally in SQLite.

## Version History

### v5.1.0

- Foundation Release
- Offline Piper TTS
- Session Settings
- Mouse Support
- Git Integration

### v5.0.0

- Rename Ed5k to JK English Coach

## Roadmap

- Favorite Words
- AI Examples
- Sentence Mode
- Shadowing Mode
- AI Quiz
- Search Function

## License

MIT License
