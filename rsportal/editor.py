import os
import subprocess
import tempfile
from typing import Tuple


def open_editor(initial_text: str = "") -> str:
    """Open user's editor ($EDITOR) to edit multi-line text and return content.

    On Windows, falls back to notepad if $EDITOR is not set.
    """
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "vi")

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".tmp", mode="w+", encoding="utf-8"
    ) as tf:
        path = tf.name
        if initial_text:
            tf.write(initial_text)
            tf.flush()

    try:
        # Open the editor and wait
        subprocess.call([editor, path])
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def parse_title_and_description(content: str) -> Tuple[str, str]:
    lines = [line.rstrip("\n") for line in content.splitlines()]
    title = lines[0].strip() if lines else ""
    description = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    return title, description
