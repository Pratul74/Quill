from rich import box
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from quill.models.snapshot import RepositorySnapshot

MAX_ROWS = 12

EXT_COLORS = {
    ".py": "#4b8bbe", ".js": "#f7df1e", ".ts": "#3178c6", ".tsx": "#3178c6",
    ".json": "#cbcb41", ".md": "#a47dff", ".toml": "#9c4221", ".yml": "#cb171e",
    ".yaml": "#cb171e", ".html": "#e34c26", ".css": "#563d7c", ".rs": "#dea584",
    ".go": "#00add8", ".sh": "#89e051",
}


def _bar(additions: int, deletions: int, scale: int, width: int) -> Text:
    """Proportional green/red bar. `scale` is the size that fills the full width."""
    total = additions + deletions
    if not total or not scale:
        return Text("░" * width, style="bright_black")

    filled = max(1, round(total / scale * width))
    green = round(filled * additions / total)
    red = filled - green
    if additions and green == 0:
        green, red = 1, max(red - 1, 0)
    if deletions and red == 0:
        red, green = 1, max(green - 1, 0)

    return Text.assemble(
        ("█" * green, "success"),
        ("█" * red, "error"),
        ("░" * max(width - green - red, 0), "bright_black"),
    )


def _file_cell(path: str) -> Text:
    path = path.replace("\\", "/")
    directory, _, name = path.rpartition("/")
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    dot_color = EXT_COLORS.get(suffix, "bright_black")

    cell = Text(no_wrap=True, overflow="ellipsis")
    cell.append("● ", style=dot_color)
    if directory:
        cell.append(f"{directory}/", style="bright_black")
    cell.append(name, style="bold white")
    return cell


def repository_panel(snapshot: RepositorySnapshot) -> Panel:
    info, diff, status = snapshot.info, snapshot.diff, snapshot.status

    ready = status.can_create_messages
    badge = (
        Text(" ✔ READY ", style="bold black on green")
        if ready
        else Text(" ! NEEDS ATTENTION ", style="bold black on yellow")
    )

    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column(style="subtitle", no_wrap=True)
    grid.add_column(ratio=1, overflow="ellipsis", no_wrap=True)

    repo = Text.assemble((info.name, "bold white"), ("   ", ""), (str(info.root_path), "bright_black"))
    branch = Text.assemble(
        ("> ", "info"),
        (str(info.current_branch), "info.bold"),
        ("   ◆ ", "bright_black"),
        (str(info.head_commit), "bright_black"),
    )
    staged = Text.assemble(
        (f"{len(diff.files)}", "bold white"),
        (" files   ", "bright_black"),
        (f"+{diff.additions}", "success.bold"),
        ("  ", ""),
        (f"-{diff.deletions}", "error.bold"),
        ("   ", ""),
    )
    staged.append_text(_bar(diff.additions, diff.deletions, diff.additions + diff.deletions, 24))

    grid.add_row("REPOSITORY", repo)
    grid.add_row("BRANCH", branch)
    grid.add_row("STAGED", staged)

    return Panel(
        grid,
        title=Text.assemble(("✦ ", "info"), ("WORKSPACE", "bold white")),
        title_align="left",
        subtitle=badge,
        subtitle_align="right",
        border_style="border",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def changes_panel(snapshot: RepositorySnapshot) -> Panel:
    diff = snapshot.diff
    title = Text.assemble(("◈ ", "info"), ("CHANGES IN THIS COMMIT", "bold white"))

    if not diff.files:
        message = Text.assemble(
            ("Nothing staged yet.  ", "warning"),
            ("Run ", "bright_black"),
            ("git add <files>", "bold info"),
            (" and then ", "bright_black"),
            ("quill", "bold info"),
            (" again.", "bright_black"),
        )
        return Panel(
            message, title=title, title_align="left",
            border_style="bright_black", box=box.ROUNDED, padding=(1, 2),
        )

    files = list(snapshot.changed_files)
    shown, hidden = files[:MAX_ROWS], len(files) - len(files[:MAX_ROWS])
    scale = max((f.additions + f.deletions for f in files), default=0)

    table = Table(box=None, expand=True, padding=(0, 1), show_edge=False,
                  header_style="subtitle", show_header=True)
    table.add_column("FILE", ratio=1, no_wrap=True, overflow="ellipsis")
    table.add_column("+", justify="right", style="success", no_wrap=True)
    table.add_column("-", justify="right", style="error", no_wrap=True)
    table.add_column("", no_wrap=True, min_width=12)

    for f in shown:
        table.add_row(
            _file_cell(f.path),
            f"+{f.additions}",
            f"-{f.deletions}",
            _bar(f.additions, f.deletions, scale, 12),
        )

    if hidden:
        table.add_row(Text(f"… and {hidden} more", style="bright_black italic"), "", "", "")

    footer = Text.assemble(
        (f" {len(files)} files ", "bright_black"),
        (f" +{diff.additions} ", "bold success"),
        (f" -{diff.deletions} ", "bold error"),
    )

    return Panel(
        table,
        title=title,
        title_align="left",
        subtitle=footer,
        subtitle_align="right",
        border_style="bright_black",
        box=box.ROUNDED,
        padding=(1, 2),
    )
