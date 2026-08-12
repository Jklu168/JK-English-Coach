# CHANGELOG

## v5.2.0 - 2026-08-11

### Changed

- Changed playback priority to gTTS MP3 first, then Piper WAV, then Piper MP3.
- Added shared Windows-safe gTTS filename handling for download and playback lookup.
- Updated audio status and verification output to report gTTS and Piper independently.
- Retained both complete audio libraries; gTTS provides preferred pronunciation quality and Piper remains the fully offline fallback.

## v5.0.1 - 2026-07-01

### Changed

- Changed default audio cache format to WAV for Piper.
- Piper is now the default bulk audio generation engine.
- Existing MP3 cache remains supported.
- gTTS kept as fallback only due to HTTP 429 rate limits during bulk generation.

## v5.0.0 - 2026-07-01

First public release as **JK English Coach**.

### Added

- SQLite database `jk_english.db`
- Review Today mode
- New Words mode
- Random by Difficulty mode
- Again / Good / Easy spaced repetition
- Daily learning statistics
- Dashboard
- Audio Build System
- GitHub-ready project structure

### Changed

- Project renamed from Ed5k to JK English Coach
- Main app moved to `src/main.py`
- Database renamed from `ed5k_words.db` to `jk_english.db`

### Archived

- Historical Ed5k scripts moved to `Archive/Scripts`
- Historical prompts moved to `Archive/Prompts`
