from rich.panel import Panel
from rich.text import Text


def show_banner() -> Panel:
    title = Text.assemble(("✦  ", "bright_cyan"), ("QUILL", "bold bright_cyan"), ("  /  ", "bright_black"), ("AI COMMIT ASSISTANT", "bold white"))
    subtitle = Text("Thoughtful commit messages, grounded in your staged diff.", style="bright_black")
    return Panel.fit(f"{title}\n{subtitle}", border_style="bright_blue", padding=(0, 2))
