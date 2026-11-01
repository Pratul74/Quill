# quill/ui/theme.py
from rich.theme import Theme

# Palette: every color is a fixed hex value, so it looks the same in every terminal.
INK = "#14151f"      # dark text on colored badges
TEXT = "#e6e6f0"
MUTED = "#7f849c"
FAINT = "#3b3f55"    # secondary borders, rules, empty bar segments
PURPLE = "#7c5cff"
LILAC = "#a47dff"
GREEN = "#5fd787"
YELLOW = "#ffd866"
RED = "#ff6b81"

TYPE_COLORS = {
    "feat": GREEN, "fix": RED, "docs": "#6cb6ff", "style": "#e58fff",
    "refactor": "#5ccfe6", "perf": YELLOW, "test": "#ffb86c",
    "build": MUTED, "ci": MUTED, "chore": MUTED, "revert": RED,
}


def type_badge(kind: str) -> str:
    return f"bold {INK} on {TYPE_COLORS.get(kind.lower(), MUTED)}"

theme = Theme({
    "text": TEXT,
    "title": f"bold {TEXT}",
    "subtitle": MUTED,
    "muted": MUTED,
    "muted.italic": f"italic {MUTED}",
    "faint": FAINT,

    "logo": f"bold {PURPLE}",
    "border": PURPLE,
    "border.muted": FAINT,
    "link": f"underline {LILAC}",

    "success": GREEN,
    "warning": YELLOW,
    "error": RED,
    "info": LILAC,
    "success.bold": f"bold {GREEN}",
    "warning.bold": f"bold {YELLOW}",
    "error.bold": f"bold {RED}",
    "info.bold": f"bold {LILAC}",

    "badge.success": f"bold {INK} on {GREEN}",
    "badge.warning": f"bold {INK} on {YELLOW}",
    "badge.error": f"bold {INK} on {RED}",
    "badge.info": f"bold {INK} on {LILAC}",
    "badge.muted": f"bold {TEXT} on {FAINT}",

    "logo.1": "bold #b794ff",
    "logo.2": f"bold {LILAC}",
    "logo.3": "bold #9166ff",
    "logo.4": f"bold {PURPLE}",
    "logo.5": "bold #6a4cf0",
    "logo.6": "bold #583ad6",

    "prompt.choices": LILAC,
    "prompt.default": f"bold {LILAC}",
    "prompt.invalid": RED,
    "prompt.invalid.choice": RED,
    "rule.line": FAINT,
    "status.spinner": LILAC,
    "bar.complete": PURPLE,
    "bar.finished": GREEN,
    "bar.pulse": LILAC,
    "progress.description": TEXT,
    "progress.percentage": LILAC,
})