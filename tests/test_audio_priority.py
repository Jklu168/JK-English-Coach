import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from audio_utils import safe_filename
from tts_engine import (
    existing_audio_path_for_word,
    existing_piper_audio_path_for_word,
    gtts_audio_path_for_word,
)


class AudioPriorityTests(unittest.TestCase):
    def test_shared_filename_rule_matches_downloader_output(self):
        self.assertEqual(safe_filename("how about?"), "how about_")
        self.assertEqual(safe_filename("中文 phrase. "), "中文 phrase")
        self.assertEqual(safe_filename("...   "), "_")

    def test_gtts_path_uses_shared_safe_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = gtts_audio_path_for_word("how about?", directory)
            self.assertEqual(path, Path(directory) / "how about_.mp3")

    def test_lookup_prefers_gtts_then_piper_wav_then_piper_mp3(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gtts_dir = root / "gtts"
            piper_dir = root / "piper"
            gtts_dir.mkdir()
            piper_dir.mkdir()

            gtts = gtts_audio_path_for_word("normal word", gtts_dir)
            wav = piper_dir / "normal_word.wav"
            mp3 = piper_dir / "normal_word.mp3"
            mp3.write_bytes(b"piper mp3")
            self.assertEqual(existing_audio_path_for_word("normal word", piper_dir, gtts_dir), mp3)

            wav.write_bytes(b"piper wav")
            self.assertEqual(existing_audio_path_for_word("normal word", piper_dir, gtts_dir), wav)

            gtts.write_bytes(b"gtts")
            self.assertEqual(existing_audio_path_for_word("normal word", piper_dir, gtts_dir), gtts)

    def test_zero_byte_files_are_not_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gtts_dir = root / "gtts"
            piper_dir = root / "piper"
            gtts_dir.mkdir()
            piper_dir.mkdir()
            gtts_audio_path_for_word("word", gtts_dir).touch()
            (piper_dir / "word.wav").touch()
            self.assertIsNone(existing_audio_path_for_word("word", piper_dir, gtts_dir))

    def test_piper_lookup_is_independent_of_gtts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gtts_dir = root / "gtts"
            piper_dir = root / "piper"
            gtts_dir.mkdir()
            piper_dir.mkdir()
            gtts_audio_path_for_word("word", gtts_dir).write_bytes(b"gtts")
            wav = piper_dir / "word.wav"
            wav.write_bytes(b"piper")
            self.assertEqual(existing_piper_audio_path_for_word("word", piper_dir), wav)


if __name__ == "__main__":
    unittest.main()
