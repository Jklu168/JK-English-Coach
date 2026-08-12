"""Shared filename rules for JK English Coach audio files."""


WINDOWS_INVALID_FILENAME_CHARS = '<>:"/\\|?*'


def safe_filename(text):
    """Return the gTTS filename stem for vocabulary text."""
    translation = str.maketrans({character: "_" for character in WINDOWS_INVALID_FILENAME_CHARS})
    sanitized = text.translate(translation).rstrip(" .")
    return sanitized or "_"
