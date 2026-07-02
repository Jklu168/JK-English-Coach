import hashlib
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from gtts import gTTS


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AUDIO_CACHE_DIR = PROJECT_ROOT / "audio_cache"
LOG_DIR = PROJECT_ROOT / "logs"
AUDIO_BUILD_LOG_PATH = LOG_DIR / "audio_build.log"
LOCAL_PIPER_EXE = PROJECT_ROOT / "tools" / "piper" / "piper.exe"
LOCAL_PIPER_MODEL_DIR = PROJECT_ROOT / "models" / "piper"


def safe_audio_stem(text):
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_-")
    if cleaned:
        return cleaned
    digest = hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()[:10]
    return f"word_{digest}"


def audio_wav_path_for_word(word, audio_dir=AUDIO_CACHE_DIR):
    return Path(audio_dir) / f"{safe_audio_stem(word)}.wav"


def audio_mp3_path_for_word(word, audio_dir=AUDIO_CACHE_DIR):
    return Path(audio_dir) / f"{safe_audio_stem(word)}.mp3"


def preferred_audio_path_for_word(word, engine_name="piper", audio_dir=AUDIO_CACHE_DIR):
    return audio_wav_path_for_word(word, audio_dir) if (engine_name or "").lower() == "piper" else audio_mp3_path_for_word(word, audio_dir)


def existing_audio_path_for_word(word, audio_dir=AUDIO_CACHE_DIR):
    wav_path = audio_wav_path_for_word(word, audio_dir)
    if wav_path.exists() and wav_path.stat().st_size > 0:
        return wav_path
    mp3_path = audio_mp3_path_for_word(word, audio_dir)
    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        return mp3_path
    return None


def audio_path_for_word(word, audio_dir=AUDIO_CACHE_DIR):
    return audio_wav_path_for_word(word, audio_dir)


def log_audio_build(message):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIO_BUILD_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{message}\n")


class BaseTTS(ABC):
    name = "Base"

    @abstractmethod
    def is_available(self):
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text, output_path):
        raise NotImplementedError


class PiperTTS(BaseTTS):
    name = "Piper"

    def __init__(self, executable=None, model_path=None):
        self.executable = executable or os.environ.get("PIPER_EXE") or self._find_local_executable() or shutil.which("piper")
        self.model_path = model_path or os.environ.get("PIPER_MODEL") or self._find_local_model()

    @staticmethod
    def _find_local_executable():
        return str(LOCAL_PIPER_EXE) if LOCAL_PIPER_EXE.exists() else None

    @staticmethod
    def _find_local_model():
        if not LOCAL_PIPER_MODEL_DIR.exists():
            return None
        models = sorted(LOCAL_PIPER_MODEL_DIR.glob("*.onnx"))
        medium = [m for m in models if "medium" in m.name.lower()]
        return str((medium or models)[0]) if models else None

    def is_available(self):
        return bool(self.executable and self.model_path and Path(self.model_path).exists())

    def synthesize(self, text, output_path):
        if not self.is_available():
            raise RuntimeError("Piper executable or model is not available")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [self.executable, "--model", self.model_path, "--output_file", str(output_path)],
            input=text,
            text=True,
            encoding="utf-8",
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


class CoquiTTS(BaseTTS):
    name = "Coqui TTS"

    def __init__(self, executable=None):
        self.executable = executable or os.environ.get("COQUI_TTS_EXE") or shutil.which("tts")

    def is_available(self):
        return bool(self.executable)

    def synthesize(self, text, output_path):
        if not self.is_available():
            raise RuntimeError("Coqui TTS command is not available")
        subprocess.run([self.executable, "--text", text, "--out_path", str(output_path)], check=True)


class GTTSTTS(BaseTTS):
    name = "gTTS"

    def is_available(self):
        return True

    def synthesize(self, text, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gTTS(text=text, lang="en").save(str(output_path))


def convert_wav_to_mp3(wav_path, mp3_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to convert Piper wav output to mp3")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav_path), str(mp3_path)], check=True)


def get_tts_engine(engine_name="auto"):
    name = (engine_name or "auto").lower()
    engines = {"piper": PiperTTS, "coqui": CoquiTTS, "gtts": GTTSTTS}
    if name != "auto":
        engine = engines[name]()
        if not engine.is_available():
            raise RuntimeError(f"Requested TTS engine is not available: {engine.name}")
        return engine
    for cls in (PiperTTS, CoquiTTS, GTTSTTS):
        engine = cls()
        if engine.is_available():
            return engine
    raise RuntimeError("No TTS engine is available")
