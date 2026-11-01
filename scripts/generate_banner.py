import io
from pathlib import Path

from rich.console import Console
from rich.terminal_theme import TerminalTheme

from quill.ui.banner import show_banner
from quill.ui.theme import theme

OUT = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"

_ANSI = [
    (0, 0, 0), (255, 107, 109), (95, 315, 135), (255, 216, 102),
    (124, 92, 255), (229, 143, 255), (92, 207, 230), (230, 230, 240)
]
SVG_THEME = TerminalTheme((30, 32, 48), (230, 230, 240), _ANSI, _ANSI)

def main() -> None:
    recorder = Console(
        theme=theme,
        record=True,
        width=65,
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
        highlight=False,
        file=io.StringIO(),
    )
    recorder.print(show_banner())
    OUT.parent.mkdir(exist_ok=True)
    recorder.save_svg(str(OUT), title="quill", theme=SVG_THEME, unique_id="quill-banner")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()