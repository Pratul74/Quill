import sys

from rich.console import Console
from quill.ui.theme import theme

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

console = Console(theme=theme, legacy_windows=False)
