import argparse
import csv
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from tts_engine import AUDIO_CACHE_DIR, audio_mp3_path_for_word, audio_wav_path_for_word, get_tts_engine, log_audio_build, preferred_audio_path_for_word

CSV_PATH = PROJECT_ROOT / "data" / "Ed5k_final_optimized.csv"
DB_PATH = PROJECT_ROOT / "data" / "jk_english.db"


def load_words_from_db():
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    try:
        return [r[0].strip() for r in conn.execute("SELECT english FROM words ORDER BY english") if r[0]]
    finally:
        conn.close()


def load_words_from_csv():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return [r[0].strip() for r in csv.reader(f)][1:]


def load_all_words():
    seen, result = set(), []
    for word in load_words_from_db() or load_words_from_csv():
        if word and word.lower() not in seen:
            seen.add(word.lower())
            result.append(word)
    return result


def is_rate_limited_error(exc):
    return "429" in str(exc) or "Too Many Requests" in str(exc)


def is_valid_audio_file(path):
    return path.exists() and path.stat().st_size > 0


def build_one(word, engine_name, engine_factory, retry_count, force=False, force_wav=False, retry_delay=0.0, throttle_delay=0.0):
    wav_path = audio_wav_path_for_word(word, AUDIO_CACHE_DIR)
    mp3_path = audio_mp3_path_for_word(word, AUDIO_CACHE_DIR)
    path = preferred_audio_path_for_word(word, engine_name, AUDIO_CACHE_DIR)

    if is_valid_audio_file(wav_path) and not force:
        return "skipped", word, None
    if is_valid_audio_file(mp3_path) and not force and not force_wav:
        return "skipped", word, None
    if is_valid_audio_file(path) and force:
        return "skipped", word, None
    last_error = None
    for attempt in range(1, retry_count + 1):
        try:
            if throttle_delay:
                time.sleep(throttle_delay)
            engine_factory().synthesize(word, path)
            if path.exists() and path.stat().st_size > 0:
                return "generated", word, None
            raise RuntimeError(f"TTS created an empty {path.suffix} file")
        except Exception as exc:
            last_error = exc
            log_audio_build(f"{word}\n{engine_name} failed\nRetry {attempt}: {type(exc).__name__}: {exc}")
            if is_rate_limited_error(exc):
                log_audio_build(f"{word}\nRATE_LIMITED")
                return "rate_limited", word, exc
            if attempt < retry_count and retry_delay:
                time.sleep(retry_delay * attempt)
    log_audio_build(f"{word}\nFAILED")
    return "failed", word, last_error


def print_progress(word, done, total, skipped, generated, failed, engine):
    print("\033[2J\033[H", end="")
    print("Building Audio Cache\n")
    print(f"Word:\n{word}\n")
    print(f"Progress:\n{done} / {total}\n")
    print(f"Skipped:\n{skipped}\n")
    print(f"Generated:\n{generated}\n")
    print(f"Failed:\n{failed}\n")
    print(f"Engine:\n{engine}")


def main():
    parser = argparse.ArgumentParser(description="Build JK English Coach audio cache.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--retry", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=0.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--engine", choices=["auto", "piper", "coqui", "gtts"], default="piper")
    parser.add_argument("--word", action="append")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--force-wav", action="store_true", help="Generate WAV even when an MP3 already exists.")
    args = parser.parse_args()

    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_tts_engine(args.engine)
    words = args.word or load_all_words()
    total = len(words)
    if not args.force:
        missing = []
        for word in words:
            wav_exists = is_valid_audio_file(audio_wav_path_for_word(word))
            mp3_exists = is_valid_audio_file(audio_mp3_path_for_word(word))
            if wav_exists:
                continue
            if mp3_exists and not args.force_wav:
                continue
            missing.append(word)
        skipped = total - len(missing)
        words = missing
    else:
        skipped = 0
    if args.limit:
        words = words[: args.limit]

    counts = {"done": skipped, "skipped": skipped, "generated": 0, "failed": 0}
    print_progress("-", counts["done"], total, skipped, 0, 0, engine.name)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = [
            executor.submit(build_one, w, engine.name, lambda: get_tts_engine(args.engine), args.retry, args.force, args.force_wav, args.retry_delay, args.delay)
            for w in words
        ]
        for future in as_completed(futures):
            status, word, _ = future.result()
            counts["done"] += 1
            if status == "rate_limited":
                counts["failed"] += 1
                print_progress(word, counts["done"], total, counts["skipped"], counts["generated"], counts["failed"], engine.name)
                print("\nRate limit detected. Stop now and retry later.")
                executor.shutdown(wait=False, cancel_futures=True)
                return
            counts[status] += 1
            print_progress(word, counts["done"], total, counts["skipped"], counts["generated"], counts["failed"], engine.name)
    print("\nAudio build finished.")


if __name__ == "__main__":
    main()
