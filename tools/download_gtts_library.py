"""Download the project's vocabulary as a resumable gTTS MP3 library."""

import argparse
import csv
import logging
import random
import sys
import time
from pathlib import Path

from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from audio_utils import safe_filename

VOCABULARY_CSV = PROJECT_ROOT / "data" / "Ed5k_final_optimized.csv"
AUDIO_DIR = PROJECT_ROOT / "audio_cache_gtts"
LOG_FILE = PROJECT_ROOT / "logs" / "gtts_download.log"
RETRY_DELAYS = (10, 20, 40)
WINDOWS_PATH_ERROR_CODES = {123, 161, 206, 267}


def audio_path(word):
    return AUDIO_DIR / f"{safe_filename(word)}.mp3"


def temporary_path(destination):
    return destination.with_suffix(destination.suffix + ".part")


def is_windows_path_error(error):
    return isinstance(error, OSError) and getattr(error, "winerror", None) in WINDOWS_PATH_ERROR_CODES


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Download missing gTTS MP3 files for data/Ed5k_final_optimized.csv."
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing MP3 files")
    parser.add_argument("--limit", type=int, help="process at most N words")
    parser.add_argument("--start", type=int, default=1, help="start at 1-based vocabulary row N")
    parser.add_argument("--delay-min", type=float, default=1.5)
    parser.add_argument("--delay-max", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--batch-sleep-min", type=float, default=300.0)
    parser.add_argument("--batch-sleep-max", type=float, default=600.0)
    args = parser.parse_args(argv)
    validate_args(parser, args)
    return args


def validate_args(parser, args):
    if args.start < 1:
        parser.error("--start must be at least 1")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.delay_min < 0 or args.delay_max < args.delay_min:
        parser.error("download delays must be non-negative and max must be >= min")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.batch_sleep_min < 0 or args.batch_sleep_max < args.batch_sleep_min:
        parser.error("batch delays must be non-negative and max must be >= min")


def load_words(csv_path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return []

    header = [cell.strip().lower() for cell in rows[0]]
    vocabulary_headers = ("english", "word")
    matched_header = next((name for name in vocabulary_headers if name in header), None)
    word_column = header.index(matched_header) if matched_header else 0
    data_rows = rows[1:] if matched_header else rows
    return [
        row[word_column].strip()
        for row in data_rows
        if len(row) > word_column and row[word_column].strip()
    ]


def select_words(words, start, limit):
    selected = list(enumerate(words[start - 1 :], start=start))
    return selected if limit is None else selected[:limit]


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def create_logger():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("gtts_download")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | word=%(word)s | status=%(status)s | retries=%(retries)d | elapsed=%(elapsed).2fs"
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def download_word(word, destination):
    from gtts import gTTS

    temporary = temporary_path(destination)
    try:
        gTTS(text=word, lang="en").save(str(temporary))
        temporary.replace(destination)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def download_with_retries(word, destination, downloader=download_word, sleeper=time.sleep):
    retries = 0
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            downloader(word, destination)
            return "OK", retries
        except OSError as error:
            if is_windows_path_error(error):
                return "FILE_PATH_ERROR", retries
            if attempt >= len(RETRY_DELAYS):
                return "FAIL", retries
        except Exception:
            if attempt >= len(RETRY_DELAYS):
                return "FAIL", retries

        retries += 1
        sleeper(RETRY_DELAYS[attempt])

    return "FAIL", retries


def has_future_download(selected, current_offset, force):
    if force:
        return current_offset + 1 < len(selected)
    return any(
        not audio_path(future_word).exists()
        for _, future_word in selected[current_offset + 1 :]
    )


def print_progress(row_number, total, counts, started_at, processed, selected_total):
    elapsed = time.monotonic() - started_at
    remaining = max(0, selected_total - processed)
    eta = (elapsed / processed * remaining) if processed else 0
    tqdm.write(
        f"[{row_number}/{total}] Downloaded : {counts['downloaded']} | "
        f"Skipped : {counts['skipped']} | Failed : {counts['failed']} | "
        f"Elapsed : {format_duration(elapsed)} | ETA : {format_duration(eta)}"
    )


def run(args):
    words = load_words(VOCABULARY_CSV)
    selected = select_words(words, args.start, args.limit)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    logger = create_logger()
    counts = {"downloaded": 0, "skipped": 0, "failed": 0}
    started_at = time.monotonic()
    downloads_since_batch = 0

    with tqdm(total=len(words), initial=min(args.start - 1, len(words)), unit="word") as progress:
        for offset, (row_number, word) in enumerate(selected):
            item_started = time.monotonic()
            destination = audio_path(word)
            retries = 0
            status = None

            try:
                destination_exists = destination.exists()
            except OSError:
                destination_exists = False
                status = "FILE_PATH_ERROR"

            if status == "FILE_PATH_ERROR":
                counts["failed"] += 1
            elif destination_exists and not args.force:
                status = "SKIP"
                counts["skipped"] += 1
            else:
                status, retries = download_with_retries(word, destination)
                if status == "OK":
                    counts["downloaded"] += 1
                else:
                    counts["failed"] += 1
                if status != "FILE_PATH_ERROR":
                    downloads_since_batch += 1

            item_elapsed = time.monotonic() - item_started
            logger.info(
                "result",
                extra={
                    "word": word,
                    "status": status,
                    "retries": retries,
                    "elapsed": item_elapsed,
                },
            )
            tqdm.write(f"{status} {word}")
            progress.update(1)
            print_progress(row_number, len(words), counts, started_at, offset + 1, len(selected))

            if status in {"OK", "FAIL"} and has_future_download(selected, offset, args.force):
                time.sleep(random.uniform(args.delay_min, args.delay_max))
            if (
                downloads_since_batch >= args.batch_size
                and has_future_download(selected, offset, args.force)
            ):
                time.sleep(random.uniform(args.batch_sleep_min, args.batch_sleep_max))
                downloads_since_batch = 0

    elapsed = time.monotonic() - started_at
    processed = sum(counts.values())
    success_rate = (
        100.0 * (counts["downloaded"] + counts["skipped"]) / processed if processed else 0.0
    )
    print("----------------------------------")
    print(f"Total words : {processed}")
    print(f"Downloaded  : {counts['downloaded']}")
    print(f"Skipped     : {counts['skipped']}")
    print(f"Failed      : {counts['failed']}")
    print(f"Elapsed time: {format_duration(elapsed)}")
    print(f"Success rate: {success_rate:.2f}%")
    print("----------------------------------")


def main():
    args = parse_args()
    try:
        run(args)
    except FileNotFoundError as error:
        raise SystemExit(f"Vocabulary CSV not found: {error.filename}") from error


if __name__ == "__main__":
    main()
