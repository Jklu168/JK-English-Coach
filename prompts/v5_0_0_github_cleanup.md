# Codex Prompt: Prepare JK English Coach v5.0.0 for GitHub

請協助整理目前 `Ed5k_v5_final.py` 專案，準備上傳 GitHub。

目標：
將專案正式命名為 **JK English Coach**，版本定為 **v5.0.0**，並整理專案目錄，把舊版與暫時不用的檔案移到 Archive。

---

## 1. Project Rename

請將專案名稱統一改為：

```python
APP_NAME = "JK English Coach"
APP_VERSION = "v5.0.0"
```

pygame 視窗標題改為：

```python
pygame.display.set_caption(f"{APP_NAME} {APP_VERSION}")
```

顯示：

```text
JK English Coach v5.0.0
```

---

## 2. Database Rename

請將 SQLite 檔名由：

```text
ed5k_words.db
```

改為：

```text
jk_english.db
```

程式內所有引用同步更新。

若舊的 `ed5k_words.db` 已存在，請提供安全遷移邏輯：

```text
如果 jk_english.db 不存在，但 ed5k_words.db 存在，
則複製 ed5k_words.db → jk_english.db，
並保留原檔，不直接刪除。
```

---

## 3. Version History

程式開頭改為：

```python
# ============================================================
# JK English Coach
# Version History
# ============================================================
```

保留 v1 ~ v5 原本紀錄，並新增：

```text
# v5.0.0 2026-07-01 by Codex
# - Project officially renamed to JK English Coach.
# - SQLite database renamed to jk_english.db.
# - Repository prepared as jk-english-coach.
# - Added GitHub-ready README, CHANGELOG, TODO, and project cleanup.
# - Moved historical or unused files to Archive.
```

請在 v1 紀錄補一句：

```text
# - Originally developed as Ed5k.
```

---

## 4. Main File Rename

請將主程式整理為：

```text
src/main.py
```

若目前只有單檔，也可以先保留單檔架構，但至少改成：

```text
src/main.py
```

並確認可由專案根目錄執行：

```bash
python src/main.py
```

路徑請使用：

```python
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
```

資料路徑請指向根目錄或 data：

```python
CSV_PATH = PROJECT_ROOT / "data" / "Ed5k_final_optimized.csv"
DB_PATH = PROJECT_ROOT / "data" / "jk_english.db"
AUDIO_CACHE_DIR = PROJECT_ROOT / "audio_cache"
LOG_DIR = PROJECT_ROOT / "logs"
BACKUP_DIR = PROJECT_ROOT / "backup"
EXPORT_DIR = PROJECT_ROOT / "exports"
```

---

## 5. Minimal GitHub Project Structure

請整理成以下最小可維護結構：

```text
jk-english-coach/
│
├── README.md
├── CHANGELOG.md
├── TODO.md
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── main.py
│   └── tts_engine.py
│
├── tools/
│   ├── generate_audio.py
│   └── verify_audio_cache.py
│
├── data/
│   ├── Ed5k_final_optimized.csv
│   └── jk_english.db
│
├── audio_cache/
├── logs/
├── backup/
├── exports/
│
├── prompts/
│   └── v5_0_0_github_cleanup.md
│
└── Archive/
    ├── Scripts/
    ├── Prompts/
    ├── Database/
    └── Releases/
```

若某些檔案目前不存在，不需硬做假檔，但資料夾可建立 `.gitkeep`。

---

## 6. Archive Cleanup

請建立：

```text
Archive/
├── Scripts/
├── Prompts/
├── Database/
└── Releases/
```

整理原則：

### Historical files → Archive

舊版程式移至：

```text
Archive/Scripts/
```

例如：

```text
Ed5k_v1.py
Ed5k_v2.py
Ed5k_v3.py
Ed5k_v4_final.py
Ed5k_v5_final.py
```

注意：
`Ed5k_v5_final.py` 若已轉成 `src/main.py`，原檔可移入 Archive/Scripts 作為歷史備份。

舊 prompt 移至：

```text
Archive/Prompts/
```

舊 database 或測試 database 移至：

```text
Archive/Database/
```

舊 release zip 移至：

```text
Archive/Releases/
```

### Temporary files → Delete

以下可以刪除，不需進 Archive：

```text
__pycache__/
*.pyc
*.tmp
.DS_Store
Thumbs.db
```

### Current files → Keep

目前仍使用的檔案不要移走：

```text
src/main.py
src/tts_engine.py
tools/generate_audio.py
tools/verify_audio_cache.py
data/Ed5k_final_optimized.csv
data/jk_english.db
audio_cache/
logs/
backup/
exports/
README.md
CHANGELOG.md
TODO.md
requirements.txt
.gitignore
```

---

## 7. README.md

請建立或更新 README.md：

````markdown
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
````

## Audio Cache

The main app plays cached MP3 files only.

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

````

---

## 8. CHANGELOG.md

請建立 CHANGELOG.md：

```markdown
# CHANGELOG

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
````

---

## 9. TODO.md

請建立 TODO.md：

```markdown
# TODO

## v5.x

- [ ] Confirm GitHub project structure
- [ ] Verify `python src/main.py`
- [ ] Verify SQLite migration
- [ ] Verify audio cache path
- [ ] Add screenshots to README
- [ ] Test on Windows 11

## v6 Ideas

- [ ] AI example sentences
- [ ] Quiz mode
- [ ] Search word
- [ ] Favorite words
- [ ] Export learning report
```

---

## 10. requirements.txt

請建立 requirements.txt：

```text
pygame
gTTS
```

若目前仍使用 `tts_engine.py`，請依實際內容補充，例如：

```text
pyttsx3
```

但若不是必須套件，請不要強制列入。

---

## 11. .gitignore

請建立 .gitignore：

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# OS
.DS_Store
Thumbs.db

# Runtime data
logs/*.log
backup/*
exports/*
*.tmp

# SQLite temporary files
*.db-journal
*.db-wal
*.db-shm

# Optional: keep database private unless user chooses to publish
# data/*.db

# Audio cache can be large; user may decide whether to commit
# audio_cache/*
```

注意：
不要預設忽略 `data/Ed5k_final_optimized.csv`，因為這是目前必要資料來源。
是否忽略 `data/jk_english.db` 和 `audio_cache/`，請用註解保留選項，不要直接忽略。

---

## 12. Path Compatibility

請確認所有 script 路徑都能從專案根目錄執行。

必須通過：

```bash
python src/main.py
python tools/generate_audio.py
python tools/verify_audio_cache.py
```

所有路徑都應以 `PROJECT_ROOT` 為基準，不要依賴目前工作目錄。

---

## 13. Functionality Must Not Change

這次是 GitHub 前整理與命名重構，不要改變核心功能。

必須保留：

* Review Today
* New Words
* Random by Difficulty
* Again / Good / Easy
* Dashboard
* Audio Cache
* SQLite
* Daily Stats
* Keyboard shortcuts
* Error screen
* logs/error.log

---

## 14. Final Verification

完成後請確認：

```text
[ ] APP_NAME = JK English Coach
[ ] APP_VERSION = v5.0.0
[ ] pygame title shows JK English Coach v5.0.0
[ ] DB_PATH uses data/jk_english.db
[ ] old ed5k_words.db can migrate safely
[ ] src/main.py runs
[ ] tools/generate_audio.py path works
[ ] tools/verify_audio_cache.py path works
[ ] README.md created
[ ] CHANGELOG.md created
[ ] TODO.md created
[ ] requirements.txt created
[ ] .gitignore created
[ ] Archive folders created
[ ] old scripts moved to Archive/Scripts
[ ] temporary files removed
[ ] no existing feature is broken
```

請直接完成檔案修改，不要只提供片段 patch。
