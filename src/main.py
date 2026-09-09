# ============================================================
# JK English Coach
# Version History
# ============================================================
# v1 2025-09-21 by JK
# - Initial English word learning tool using CSV data and pygame.
# - Originally developed as Ed5k.
#
# v5.0.0 2026-07-01 by Codex
# - Project officially renamed to JK English Coach.
# - SQLite database renamed to jk_english.db.
# - Repository prepared as jk-english-coach.
# - Added GitHub-ready README, CHANGELOG, TODO, and project cleanup.
# ============================================================

import asyncio
import csv
import datetime as dt
import os
import random
import shutil
import sqlite3
from pathlib import Path

import pygame
from tts_engine import (
    GTTS_AUDIO_CACHE_DIR,
    existing_audio_path_for_word,
    existing_piper_audio_path_for_word,
    gtts_audio_path_for_word,
)


APP_NAME = "JK English Coach"
APP_VERSION = "v5.2.0"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / "data" / "Ed5k_final_optimized.csv"
DB_PATH = PROJECT_ROOT / "data" / "jk_english.db"
OLD_DB_PATHS = [PROJECT_ROOT / "data" / "ed5k_words.db", PROJECT_ROOT / "ed5k_words.db"]
AUDIO_CACHE_DIR = PROJECT_ROOT / "audio_cache"
LOG_DIR = PROJECT_ROOT / "logs"
BACKUP_DIR = PROJECT_ROOT / "backup"
EXPORT_DIR = PROJECT_ROOT / "exports"
ERROR_LOG_PATH = LOG_DIR / "error.log"

BASE_W, BASE_H = 760, 540
FPS = 60

WHITE = (255, 255, 255)
BG = (248, 249, 250)
BLUE = (0, 51, 102)
WORD_BLUE = (0, 0, 220)
TEXT = (45, 45, 45)
MUTED = (115, 115, 115)
RED = (200, 30, 30)
ORANGE = (210, 115, 20)
BTN_BG = (240, 240, 240)
BTN_BORDER = (180, 180, 180)

current_play_id = 0
MIXER_READY = False
TTS_STATUS = "Ready"


class AppError(Exception):
    pass


class SessionSettings:
    def __init__(self):
        self.auto_next_ms = 9000
        self.repeat_count = 3


class AppState:
    def __init__(self, screen):
        self.screen = screen
        self.win_w, self.win_h = screen.get_size()
        self.update_fonts()

    def update_size(self, w, h):
        self.win_w, self.win_h = max(540, w), max(420, h)
        self.update_fonts()

    def update_fonts(self):
        ratio = max(0.78, min(1.55, min(self.win_w / BASE_W, self.win_h / BASE_H)))
        self.ratio = ratio
        self.f_title = self.font(32 * ratio)
        self.f_large = self.font(56 * ratio)
        self.f_word = self.font(72 * ratio, bold=True)
        self.f_mid = self.font(25 * ratio)
        self.f_small = self.font(17 * ratio)
        self.f_btn = self.font(15 * ratio)
        self.f_tiny = self.font(13 * ratio)

    @staticmethod
    def font(size, bold=False):
        for name in ["Microsoft JhengHei", "Microsoft YaHei", "msjh", "msyh", "Arial Unicode MS"]:
            font = pygame.font.SysFont(name, int(size), bold=bold)
            if font:
                return font
        return pygame.font.SysFont(None, int(size), bold=bold)


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")


def today_text():
    return dt.date.today().isoformat()


def log_error(context, exc):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {context} | {type(exc).__name__}: {exc}\n")


def log_event(message):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] INFO: {message}\n")


def ensure_dirs():
    for path in [AUDIO_CACHE_DIR, LOG_DIR, BACKUP_DIR, EXPORT_DIR, DB_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def migrate_old_database_if_needed():
    if DB_PATH.exists():
        return
    for old_path in OLD_DB_PATHS:
        if old_path.exists():
            shutil.copy2(old_path, DB_PATH)
            log_event(f"Migrated old database from {old_path}")
            return


def init_db():
    migrate_old_database_if_needed()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT UNIQUE,
            pos TEXT,
            chinese TEXT,
            difficulty TEXT,
            learned INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            last_review TEXT,
            next_review TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            reviewed_count INTEGER DEFAULT 0,
            learned_count INTEGER DEFAULT 0,
            again_count INTEGER DEFAULT 0,
            good_count INTEGER DEFAULT 0,
            easy_count INTEGER DEFAULT 0,
            duration_sec INTEGER DEFAULT 0,
            updated_at TEXT
        )
        """
    )
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM words").fetchone()[0] == 0:
        import_csv_to_db(conn)
    return conn


def import_csv_to_db(conn):
    if not CSV_PATH.exists():
        raise AppError(f"CSV file not found: {CSV_PATH}")
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    now = now_iso()
    with conn:
        for row in rows[1:]:
            if len(row) < 4 or not row[0].strip():
                continue
            learned = 1 if len(row) >= 5 and row[4].strip().lower() == "y" else 0
            conn.execute(
                """
                INSERT OR IGNORE INTO words
                (english, pos, chinese, difficulty, learned, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(), learned, now, now),
            )


def word_from_row(row):
    return {
        "id": row["id"],
        "english": row["english"],
        "pos": row["pos"] or "",
        "chinese": row["chinese"] or "",
        "difficulty": row["difficulty"] or "",
        "review_count": int(row["review_count"] or 0),
        "correct_count": int(row["correct_count"] or 0),
        "wrong_count": int(row["wrong_count"] or 0),
        "next_review": row["next_review"],
    }


def load_due_words(conn):
    rows = conn.execute(
        "SELECT * FROM words WHERE learned=0 AND next_review IS NOT NULL AND next_review <= ? ORDER BY next_review, wrong_count DESC, difficulty DESC",
        (now_iso(),),
    ).fetchall()
    return [word_from_row(r) for r in rows]


def load_new_words(conn):
    rows = conn.execute("SELECT * FROM words WHERE learned=0 AND review_count=0 ORDER BY RANDOM()").fetchall()
    return [word_from_row(r) for r in rows]


def load_random_words_by_difficulty(conn, difficulty):
    rows = conn.execute("SELECT * FROM words WHERE learned=0 AND difficulty=? ORDER BY RANDOM()", (difficulty,)).fetchall()
    return [word_from_row(r) for r in rows]


def compute_next_review(result, previous_count):
    now = dt.datetime.now().replace(microsecond=0)
    if result == "again":
        return now + dt.timedelta(minutes=10)
    if result == "good":
        return now + dt.timedelta(days=1 if previous_count == 0 else 3 if previous_count == 1 else 7)
    return now + dt.timedelta(days=3 if previous_count == 0 else 7 if previous_count == 1 else 14)


def update_review_result(conn, word, result):
    previous = word["review_count"]
    next_review = compute_next_review(result, previous).isoformat(sep=" ")
    timestamp = now_iso()
    if result == "again":
        sql = "UPDATE words SET wrong_count=wrong_count+1, review_count=review_count+1, last_review=?, next_review=?, updated_at=? WHERE id=?"
    else:
        sql = "UPDATE words SET correct_count=correct_count+1, review_count=review_count+1, last_review=?, next_review=?, updated_at=? WHERE id=?"
    with conn:
        conn.execute(sql, (timestamp, next_review, timestamp, word["id"]))
    word["review_count"] += 1
    word["next_review"] = next_review


def mark_learned(conn, word):
    with conn:
        conn.execute("UPDATE words SET learned=1, updated_at=? WHERE id=?", (now_iso(), word["id"]))


def update_difficulty(conn, word, difficulty):
    with conn:
        conn.execute("UPDATE words SET difficulty=?, updated_at=? WHERE id=?", (difficulty, now_iso(), word["id"]))
    word["difficulty"] = difficulty


def update_daily_stats(conn, stats):
    with conn:
        conn.execute(
            """
            INSERT INTO daily_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
              reviewed_count=reviewed_count+excluded.reviewed_count,
              learned_count=learned_count+excluded.learned_count,
              again_count=again_count+excluded.again_count,
              good_count=good_count+excluded.good_count,
              easy_count=easy_count+excluded.easy_count,
              duration_sec=duration_sec+excluded.duration_sec,
              updated_at=excluded.updated_at
            """,
            (today_text(), stats["reviewed_count"], stats["learned_count"], stats["again_count"], stats["good_count"], stats["easy_count"], stats["duration_sec"], now_iso()),
        )
    log_event(f"Session summary {stats}")


def get_dashboard_stats(conn):
    row = conn.execute(
        """
        SELECT COUNT(*) total,
               SUM(CASE WHEN learned=1 THEN 1 ELSE 0 END) learned,
               SUM(CASE WHEN learned=0 THEN 1 ELSE 0 END) remaining,
               SUM(CASE WHEN learned=0 AND review_count=0 THEN 1 ELSE 0 END) new_count,
               SUM(CASE WHEN learned=0 AND next_review IS NOT NULL AND next_review <= ? THEN 1 ELSE 0 END) due
        FROM words
        """,
        (now_iso(),),
    ).fetchone()
    daily = conn.execute("SELECT * FROM daily_stats WHERE date=?", (today_text(),)).fetchone()
    words = [r[0] for r in conn.execute("SELECT english FROM words").fetchall()]
    gtts_ok = sum(
        1
        for word in words
        if (path := gtts_audio_path_for_word(word, GTTS_AUDIO_CACHE_DIR)).exists()
        and path.stat().st_size > 0
    )
    piper_ok = sum(1 for word in words if existing_piper_audio_path_for_word(word, AUDIO_CACHE_DIR))
    audio_ok = sum(
        1
        for word in words
        if existing_audio_path_for_word(word, AUDIO_CACHE_DIR, GTTS_AUDIO_CACHE_DIR)
    )
    return {
        "total_count": int(row["total"] or 0),
        "learned_count": int(row["learned"] or 0),
        "remaining_count": int(row["remaining"] or 0),
        "new_count": int(row["new_count"] or 0),
        "due_count": int(row["due"] or 0),
        "today_reviewed": int(daily["reviewed_count"]) if daily else 0,
        "today_learned": int(daily["learned_count"]) if daily else 0,
        "today_duration": int(daily["duration_sec"]) if daily else 0,
        "audio_existing": audio_ok,
        "audio_total": len(words),
        "audio_missing": max(0, len(words) - audio_ok),
        "audio_percent": int(audio_ok / len(words) * 100) if words else 0,
        "gtts_existing": gtts_ok,
        "piper_existing": piper_ok,
    }


def init_pygame():
    global MIXER_READY
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    try:
        pygame.mixer.init()
        MIXER_READY = True
    except Exception as exc:
        MIXER_READY = False
        log_error("pygame mixer init failed", exc)
    pygame.display.set_caption(f"{APP_NAME} {APP_VERSION}")


def draw_center(screen, font, text, color, center):
    surf = font.render(str(text), True, color)
    screen.blit(surf, surf.get_rect(center=center))


def learning_word_center(state):
    return state.win_w / 2, state.win_h * 0.30


def draw_button(screen, font, rect, text):
    pygame.draw.rect(screen, BTN_BG, rect, border_radius=4)
    pygame.draw.rect(screen, BTN_BORDER, rect, 1, border_radius=4)
    draw_center(screen, font, text, TEXT, rect.center)


def fmt(seconds):
    return f"{int(seconds)//60:02}:{int(seconds)%60:02}"


def wrap_text(text, font, max_w):
    lines, cur, width = [], "", 0
    for ch in str(text):
        w = font.size(ch)[0]
        if cur and width + w > max_w:
            lines.append(cur)
            cur, width = ch, w
        else:
            cur += ch
            width += w
    if cur:
        lines.append(cur)
    return lines


def stop_audio():
    if MIXER_READY:
        try:
            pygame.mixer.music.stop()
        except Exception as exc:
            log_error("pygame stop failed", exc)


async def speak_word_task(word, play_id, repeat_count):
    global TTS_STATUS
    if not MIXER_READY:
        TTS_STATUS = "No Mixer"
        return
    path = existing_audio_path_for_word(word["english"], AUDIO_CACHE_DIR)
    if not path:
        TTS_STATUS = "Missing Audio"
        log_error("audio missing", RuntimeError(f"{word['english']}; run python tools/generate_audio.py"))
        return
    try:
        TTS_STATUS = "gTTS" if path.parent == GTTS_AUDIO_CACHE_DIR else "Piper"
        for _ in range(repeat_count):
            if play_id != current_play_id:
                return
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if play_id != current_play_id:
                    stop_audio()
                    return
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.7)
    except Exception as exc:
        TTS_STATUS = "TTS Failed"
        log_error("pygame play failed", exc)


def replay(word, settings):
    global current_play_id
    current_play_id += 1
    stop_audio()
    asyncio.create_task(speak_word_task(word, current_play_id, settings.repeat_count))


def build_buttons(state):
    names = ["pause", "replay", "again", "good", "easy", "learned", "exit"]
    gap = max(4, int(8 * state.ratio))
    available_width = state.win_w - 24 - (len(names) - 1) * gap
    bw = max(64, min(int(82 * state.ratio), available_width // len(names)))
    bh = max(32, int(36 * state.ratio))
    x = (state.win_w - len(names) * bw - (len(names) - 1) * gap) // 2
    y = int(state.win_h - 54 * state.ratio)
    return {name: pygame.Rect(x + i * (bw + gap), y, bw, bh) for i, name in enumerate(names)}


def clicked_button(buttons, pos):
    for name, rect in buttons.items():
        if rect.collidepoint(pos):
            return name
    return None


def draw_mode(state, dashboard, settings, note=""):
    s = state.screen
    s.fill(BG)
    y = state.win_h * 0.10
    draw_center(s, state.f_title, f"{APP_NAME} {APP_VERSION}", BLUE, (state.win_w / 2, y))
    y += 58 * state.ratio
    lines = [
        "1. Review Today",
        "2. New Words",
        "3. Random by Difficulty",
        "",
        f"Today due: {dashboard['due_count']}   New: {dashboard['new_count']}   Learned: {dashboard['learned_count']}",
        f"Remaining: {dashboard['remaining_count']}   Total: {dashboard['total_count']}",
        f"Audio: gTTS {dashboard['gtts_existing']} / {dashboard['audio_total']}   Piper {dashboard['piper_existing']} / {dashboard['audio_total']}",
        "Primary: gTTS   Fallback: Piper",
        "Ctrl+D: Dashboard | Esc: Exit",
    ]
    for line in lines:
        draw_center(s, state.f_small, line, RED if line.startswith("D:") else TEXT, (state.win_w / 2, y))
        y += 29 * state.ratio
    y += 6 * state.ratio
    settings_lines = [
        "--------------------------------",
        "Session Settings",
        "Delay :",
        f"{settings.auto_next_ms // 1000} sec",
        "Repeat :",
        f"{settings.repeat_count} times",
        "--------------------------------",
        "Press A / D",
        "Decrease / Increase Delay",
        "Press Z / X",
        "Decrease / Increase Repeat",
    ]
    for line in settings_lines:
        color = BLUE if line == "Session Settings" else TEXT
        draw_center(s, state.f_tiny, line, color, (state.win_w / 2, y))
        y += 18 * state.ratio
    if note or dashboard["audio_missing"]:
        msg = note or f"Audio missing {dashboard['audio_missing']}. Please run python tools/generate_audio.py"
        draw_center(s, state.f_small, msg, ORANGE, (state.win_w / 2, state.win_h * 0.88))
    pygame.display.flip()


def draw_dashboard(state, dashboard):
    s = state.screen
    s.fill(BG)
    y = state.win_h * 0.12
    draw_center(s, state.f_title, f"Dashboard - {APP_NAME}", BLUE, (state.win_w / 2, y))
    y += 58 * state.ratio
    for line in [
        f"Due today: {dashboard['due_count']}",
        f"New words: {dashboard['new_count']}",
        f"Learned total: {dashboard['learned_count']}",
        f"Remaining: {dashboard['remaining_count']}",
        f"Today reviewed: {dashboard['today_reviewed']}",
        f"Today duration: {fmt(dashboard['today_duration'])}",
        f"Audio: gTTS {dashboard['gtts_existing']} / {dashboard['audio_total']}   Piper {dashboard['piper_existing']} / {dashboard['audio_total']}",
        "Primary: gTTS   Fallback: Piper",
        "Press any key or mouse to return",
    ]:
        draw_center(s, state.f_mid, line, RED if line.startswith("Press") else TEXT, (state.win_w / 2, y))
        y += 40 * state.ratio
    pygame.display.flip()


def draw_learning(state, word, idx, total, mode, paused, runtime, stats, buttons):
    s = state.screen
    s.fill(WHITE)
    s.blit(state.f_btn.render(f"Mode: {mode}", True, BLUE), (16, 12))
    s.blit(state.f_btn.render(f"Difficulty: {word['difficulty']}", True, RED), (16, 34))
    s.blit(state.f_btn.render(f"Again/Good/Easy: {stats['again_count']}/{stats['good_count']}/{stats['easy_count']}", True, MUTED), (16, 56))
    s.blit(state.f_btn.render(f"Progress: {idx+1}/{total}", True, MUTED), (state.win_w - 210, 12))
    s.blit(state.f_btn.render(f"Time: {fmt(runtime)}", True, MUTED), (state.win_w - 210, 34))
    draw_center(s, state.f_word, word["english"], WORD_BLUE, learning_word_center(state))
    for i, line in enumerate(wrap_text(f"{word['pos']}: {word['chinese']}", state.f_mid, state.win_w * 0.9)[:3]):
        draw_center(s, state.f_mid, line, TEXT, (state.win_w / 2, state.win_h * 0.49 + i * 34 * state.ratio))
    detail = f"review_count: {word['review_count']} | wrong_count: {word['wrong_count']} | next_review: {word['next_review'] or '-'} | TTS: {TTS_STATUS}"
    draw_center(s, state.f_tiny, detail, MUTED, (state.win_w / 2, state.win_h - 112 * state.ratio))
    draw_center(s, state.f_tiny, "A: Again | G: Good | E: Easy | R: Replay | S: Learned | N/Right: Next | B/Left: Back | Space: Pause | Esc: Exit", MUTED, (state.win_w / 2, state.win_h - 88 * state.ratio))
    labels = {"pause": "Resume" if paused else "Pause", "replay": "Replay", "again": "Again", "good": "Good", "easy": "Easy", "learned": "Learned", "exit": "Exit"}
    for key, label in labels.items():
        draw_button(s, state.f_btn, buttons[key], label)
    pygame.display.flip()


async def show_dashboard(state, conn):
    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
            if e.type == pygame.VIDEORESIZE:
                state.update_size(e.w, e.h)
        draw_dashboard(state, get_dashboard_stats(conn))
        await asyncio.sleep(0.08)


async def choose_difficulty(state):
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return None
            if e.type == pygame.VIDEORESIZE:
                state.update_size(e.w, e.h)
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_1, pygame.K_KP1): return "1"
                if e.key in (pygame.K_2, pygame.K_KP2): return "2"
                if e.key in (pygame.K_3, pygame.K_KP3): return "3"
        state.screen.fill(BG)
        draw_center(state.screen, state.f_title, "Random by Difficulty", BLUE, (state.win_w / 2, state.win_h * 0.28))
        draw_center(state.screen, state.f_mid, "Press 1 / 2 / 3", TEXT, (state.win_w / 2, state.win_h * 0.45))
        pygame.display.flip()
        await asyncio.sleep(0.05)


async def choose_mode(state, conn, settings):
    note = ""
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return None, None
            if e.type == pygame.VIDEORESIZE:
                state.update_size(e.w, e.h)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_d and (e.mod & pygame.KMOD_CTRL):
                    await show_dashboard(state, conn)
                elif e.key == pygame.K_a:
                    settings.auto_next_ms = max(5000, settings.auto_next_ms - 1000)
                elif e.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_KP6):
                    settings.auto_next_ms = min(20000, settings.auto_next_ms + 1000)
                elif e.key == pygame.K_z:
                    settings.repeat_count = max(1, settings.repeat_count - 1)
                elif e.key == pygame.K_x:
                    settings.repeat_count = min(5, settings.repeat_count + 1)
                elif e.key in (pygame.K_1, pygame.K_KP1):
                    words = load_due_words(conn)
                    note = "No due words. Try New Words or Random." if not words else ""
                    if words: return "Review Today", words
                elif e.key in (pygame.K_2, pygame.K_KP2):
                    words = load_new_words(conn)
                    if words: return "New Words", words
                    note = "No new words."
                elif e.key in (pygame.K_3, pygame.K_KP3):
                    d = await choose_difficulty(state)
                    if d:
                        words = load_random_words_by_difficulty(conn, d)
                        if words: return f"Random Difficulty {d}", words
                        note = f"No words for difficulty {d}."
        draw_mode(state, get_dashboard_stats(conn), settings, note)
        await asyncio.sleep(0.05)


async def run_learning(state, conn, mode, words, settings):
    global current_play_id
    idx, paused, last_idx = 0, False, -1
    start = pygame.time.get_ticks()
    word_start = start
    reviewed = set()
    stats = {"reviewed_count": 0, "learned_count": 0, "again_count": 0, "good_count": 0, "easy_count": 0, "duration_sec": 0}
    while idx < len(words):
        word = words[idx]
        buttons = build_buttons(state)
        advance = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                idx = len(words); break
            if e.type == pygame.VIDEORESIZE:
                state.update_size(e.w, e.h)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE: paused = not paused
                elif e.key == pygame.K_r and not paused: replay(word, settings)
                elif e.key in (pygame.K_n, pygame.K_RIGHT) and not paused: advance = True
                elif e.key in (pygame.K_b, pygame.K_LEFT) and not paused and idx > 0: idx -= 1; last_idx = -1
                elif e.key == pygame.K_s and not paused: mark_learned(conn, word); stats["learned_count"] += 1; advance = True
                elif e.key == pygame.K_a and not paused: update_review_result(conn, word, "again"); stats["again_count"] += 1; advance = True
                elif e.key == pygame.K_g and not paused: update_review_result(conn, word, "good"); stats["good_count"] += 1; advance = True
                elif e.key == pygame.K_e and not paused: update_review_result(conn, word, "easy"); stats["easy_count"] += 1; advance = True
                elif e.key in (pygame.K_1, pygame.K_KP1): update_difficulty(conn, word, "1")
                elif e.key in (pygame.K_2, pygame.K_KP2): update_difficulty(conn, word, "2")
                elif e.key in (pygame.K_3, pygame.K_KP3): update_difficulty(conn, word, "3")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                action = clicked_button(buttons, e.pos)
                if action == "pause":
                    paused = not paused
                elif action == "replay" and not paused:
                    replay(word, settings)
                elif action == "again" and not paused:
                    update_review_result(conn, word, "again"); stats["again_count"] += 1; advance = True
                elif action == "good" and not paused:
                    update_review_result(conn, word, "good"); stats["good_count"] += 1; advance = True
                elif action == "easy" and not paused:
                    update_review_result(conn, word, "easy"); stats["easy_count"] += 1; advance = True
                elif action == "learned" and not paused:
                    mark_learned(conn, word); stats["learned_count"] += 1; advance = True
                elif action == "exit":
                    idx = len(words); break
        if advance:
            current_play_id += 1
            stop_audio()
            idx += 1
            word_start = pygame.time.get_ticks()
            last_idx = -1
            continue
        if idx >= len(words): break
        reviewed.add(word["id"])
        runtime = (pygame.time.get_ticks() - start) // 1000
        stats["reviewed_count"] = len(reviewed)
        draw_learning(state, word, idx, len(words), mode, paused, runtime, stats, buttons)
        if not paused and last_idx != idx:
            last_idx = idx
            replay(word, settings)
        if not paused and pygame.time.get_ticks() - word_start > settings.auto_next_ms:
            current_play_id += 1
            stop_audio()
            idx += 1
            word_start = pygame.time.get_ticks()
            last_idx = -1
        await asyncio.sleep(1 / FPS)
    stats["duration_sec"] = (pygame.time.get_ticks() - start) // 1000
    update_daily_stats(conn, stats)
    return stats


async def show_summary(state, stats):
    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        state.screen.fill(BG)
        y = state.win_h * 0.18
        draw_center(state.screen, state.f_title, "Session Summary", BLUE, (state.win_w / 2, y))
        for line in [f"Reviewed: {stats['reviewed_count']}", f"Learned: {stats['learned_count']}", f"Again/Good/Easy: {stats['again_count']}/{stats['good_count']}/{stats['easy_count']}", f"Duration: {fmt(stats['duration_sec'])}", "Press any key to exit"]:
            y += 45
            draw_center(state.screen, state.f_mid, line, TEXT, (state.win_w / 2, y))
        pygame.display.flip()
        await asyncio.sleep(0.1)


async def error_screen(state, message):
    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        state.screen.fill(WHITE)
        draw_center(state.screen, state.f_title, "Startup Error", RED, (state.win_w / 2, state.win_h * 0.25))
        for i, line in enumerate(wrap_text(message, state.f_small, state.win_w * 0.86)):
            draw_center(state.screen, state.f_small, line, TEXT, (state.win_w / 2, state.win_h * 0.40 + i * 28))
        pygame.display.flip()
        await asyncio.sleep(0.1)


async def main():
    ensure_dirs()
    init_pygame()
    screen = pygame.display.set_mode((BASE_W, BASE_H), pygame.RESIZABLE)
    state = AppState(screen)
    settings = SessionSettings()
    conn = None
    try:
        log_event(f"{APP_NAME} {APP_VERSION} started")
        conn = init_db()
        mode, words = await choose_mode(state, conn, settings)
        if mode:
            stats = await run_learning(state, conn, mode, words, settings)
            await show_summary(state, stats)
    except Exception as exc:
        log_error("startup or runtime failed", exc)
        await error_screen(state, str(exc))
    finally:
        if conn:
            conn.close()
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())


