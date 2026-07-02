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

from tts_engine import AUDIO_CACHE_DIR, audio_mp3_path_for_word, audio_wav_path_for_word, get_tts_engine, log_audio_build, preferred_audio_path_for_word

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
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pygame.init()
    pygame.mixer.init()
    words = load_words()
    wav_existing = 0
    mp3_existing = 0
    any_existing = 0
    missing, corrupted = [], []
    for word in words:
        wav_path = audio_wav_path_for_word(word)
        mp3_path = audio_mp3_path_for_word(word)
        wav_ok = wav_path.exists() and wav_path.stat().st_size > 0 and playable(wav_path)
        mp3_ok = mp3_path.exists() and mp3_path.stat().st_size > 0 and playable(mp3_path)
        if wav_ok:
            wav_existing += 1
        if mp3_ok:
            mp3_existing += 1
        if wav_ok or mp3_ok:
            any_existing += 1
        elif not wav_path.exists() and not mp3_path.exists():
            missing.append(word)
        else:
            corrupted.append(word)
    if args.repair:
        engine = get_tts_engine()
        for word in missing + corrupted:
            try:
                path = preferred_audio_path_for_word(word, engine.name)
                if path.exists():
                    continue
                engine.synthesize(word, path)
            except Exception as exc:
                log_audio_build(f"{word}\nrepair failed: {type(exc).__name__}: {exc}")
    pygame.quit()
    print("Total words:")
    print(len(words))
    print("\nWAV existing:")
    print(wav_existing)
    print("\nMP3 existing:")
    print(mp3_existing)
    print("\nAny audio existing:")
    print(any_existing)
    print("\nMissing audio:")
    print(len(missing))
    print("\nCorrupted audio:")
    print(len(corrupted))


if __name__ == "__main__":
    main()
