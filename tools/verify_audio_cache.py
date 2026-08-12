import argparse
import csv
import sqlite3
import sys
from pathlib import Path

import pygame

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from tts_engine import (
    AUDIO_CACHE_DIR,
    GTTS_AUDIO_CACHE_DIR,
    audio_mp3_path_for_word,
    audio_wav_path_for_word,
    get_tts_engine,
    gtts_audio_path_for_word,
    log_audio_build,
    preferred_audio_path_for_word,
)

CSV_PATH = PROJECT_ROOT / "data" / "Ed5k_final_optimized.csv"
DB_PATH = PROJECT_ROOT / "data" / "jk_english.db"


def load_words():
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute("SELECT english FROM words ORDER BY english").fetchall()
            return [r[0] for r in rows if r[0]]
        finally:
            conn.close()
    if CSV_PATH.exists():
        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            return [r[0] for r in list(csv.reader(f))[1:] if r and r[0]]
    return []


def playable(path):
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.unload()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify JK English Coach audio cache.")
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    pygame.init()
    pygame.mixer.init()
    words = load_words()
    gtts_existing = 0
    piper_existing = 0
    playback_coverage = 0
    gtts_missing, gtts_corrupt = [], []
    piper_missing, piper_corrupt = [], []
    for word in words:
        gtts_path = gtts_audio_path_for_word(word, GTTS_AUDIO_CACHE_DIR)
        wav_path = audio_wav_path_for_word(word)
        mp3_path = audio_mp3_path_for_word(word)
        gtts_ok = gtts_path.exists() and gtts_path.stat().st_size > 0 and playable(gtts_path)
        wav_ok = wav_path.exists() and wav_path.stat().st_size > 0 and playable(wav_path)
        mp3_ok = mp3_path.exists() and mp3_path.stat().st_size > 0 and playable(mp3_path)

        if gtts_ok:
            gtts_existing += 1
        elif not gtts_path.exists():
            gtts_missing.append(word)
        else:
            gtts_corrupt.append(word)

        if wav_ok or mp3_ok:
            piper_existing += 1
        elif not wav_path.exists() and not mp3_path.exists():
            piper_missing.append(word)
        else:
            piper_corrupt.append(word)

        if gtts_ok or wav_ok or mp3_ok:
            playback_coverage += 1
    if args.repair:
        engine = get_tts_engine()
        for word in piper_missing + piper_corrupt:
            try:
                path = preferred_audio_path_for_word(word, engine.name)
                if path.exists():
                    continue
                engine.synthesize(word, path)
            except Exception as exc:
                log_audio_build(f"{word}\nrepair failed: {type(exc).__name__}: {exc}")
    pygame.quit()
    print(f"Total words : {len(words)}")
    print("\ngTTS:")
    print(f"Existing : {gtts_existing}")
    print(f"Missing  : {len(gtts_missing)}")
    print(f"Corrupt  : {len(gtts_corrupt)}")
    print("\nPiper:")
    print(f"Existing : {piper_existing}")
    print(f"Missing  : {len(piper_missing)}")
    print(f"Corrupt  : {len(piper_corrupt)}")
    print("\nPlayback coverage:")
    print(f"{playback_coverage} / {len(words)}")


if __name__ == "__main__":
    main()
