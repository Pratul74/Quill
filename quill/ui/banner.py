from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from quill.ui.console import console
from rich.panel import Panel
from rich.text import Text


GLYPHS = {
    "Q": [
        " ██████╗ ",
        "██╔═══██╗",
        "██║   ██║",
        "██║▄▄ ██║",
        "╚██████╔╝",
        " ╚══▀▀═╝ ",
    ],
    "U": [
        "██╗   ██╗",
        "██║   ██║",
        "██║   ██║",
        "██║   ██║",
        "╚██████╔╝",
        " ╚═════╝ ",
    ],
    "I": [
        "██╗",
        "██║",
        "██║",
        "██║",
        "██║",
        "╚═╝",
    ],
    "L": [
        "██╗     ",
        "██║     ",
        "██║     ",
        "██║     ",
        "███████╗",
        "╚══════╝",
    ],
}

GRADIENT = [f"logo.{i}" for i in range(1, 7)]


def build_logo(word: str = "QUILL") -> list[str]:
    rows = ["".join(GLYPHS[ch][i] for ch in word) for i in range(6)]
    width = max(len(r) for r in rows)
    return [r.ljust(width) for r in rows]


def show_banner() -> RenderableType:
    logo_rows = build_logo()
    logo_width = len(logo_rows[0])

    if console.width < logo_width + 12:
        header: list[RenderableType] = [Text("QUILL", style="logo", justify="center")]
    else:
        header = [
            Align.center(Text(row, style=style, no_wrap=True))
            for row, style in zip(logo_rows, GRADIENT)
        ]

    subtitle = Text(justify="center")
    subtitle.append("AI Commit Assistant", style="title")
    subtitle.append("\n")
    subtitle.append("Thoughtful commit messages from staged changes.", style="subtitle")

    panel = Panel(
        Group(*header, Text(""), subtitle),
        box=box.ROUNDED,
        border_style="border",
        padding=(1, 4),
        expand=False,
    )
    return Align.center(panel)
