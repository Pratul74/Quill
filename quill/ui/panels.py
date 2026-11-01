from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from quill.models.snapshot import RepositorySnapshot

MAX_ROWS = 12

EXT_COLORS = {
    ".py": "#4b8bbe", ".js": "#f7df1e", ".jsx": "#f7df1e",".ts": "#3178c6", ".tsx": "#3178c6",
    ".json": "#cbcb41", ".md": "#a47dff", ".toml": "#d08a5c", ".yml": "#e0565b",
    ".yaml": "#e0565b", ".html": "#e34c26", ".css": "#9d7fe0", ".rs": "#dea584",
    ".go": "#00add8", ".sh": "#89e051",
}


def _files(n: int) -> str:
    return f"{n} file" if n == 1 else f"{n} files"


def _bar(additions: int, deletions: int, scale: int, width: int) -> Text:
    """Proportional green/red bar. `scale` is the size that fills the full width."""
    total = additions + deletions
    if not total or not scale:
        return Text("░" * width, style="faint")

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
        ("░" * max(width - green - red, 0), "faint"),
    )


def _file_cell(path: str) -> Text:
    path = path.replace("\\", "/")
    directory, _, name = path.rpartition("/")
    suffix = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    dot_color = EXT_COLORS.get(suffix, "#7f849c")

    cell = Text(no_wrap=True, overflow="ellipsis")
    cell.append("● ", style=dot_color)
    if directory:
        cell.append(f"{directory}/", style="muted")
    cell.append(name, style="title")
    return cell


def repository_panel(snapshot: RepositorySnapshot) -> Panel:
    info, diff, status = snapshot.info, snapshot.diff, snapshot.status

    badge = (
        Text(" ✓ READY ", style="badge.success")
        if status.can_create_messages
        else Text(" ! NEEDS ATTENTION ", style="badge.warning")
    )

    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column(style="subtitle", no_wrap=True)
    grid.add_column(ratio=1, overflow="ellipsis", no_wrap=True)

    repo = Text.assemble((info.name, "title"), ("   ", ""), (str(info.root_path), "muted"))
    branch = Text.assemble(
        ("❯ ", "info"),
        (str(info.current_branch), "info.bold"),
        ("   ◆ ", "muted"),
        (str(info.head_commit), "muted"),
    )
    staged = Text.assemble(
        (_files(len(diff.files)) + "   ", "title"),
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
        title=Text.assemble(("✦ ", "info"), ("WORKSPACE", "title")),
        title_align="left",
        subtitle=badge,
        subtitle_align="right",
        border_style="border",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def changes_panel(snapshot: RepositorySnapshot) -> Panel:
    diff = snapshot.diff
    title = Text.assemble(("◈ ", "info"), ("CHANGES IN THIS COMMIT", "title"))

    if not diff.files:
        message = Text.assemble(
            ("Nothing staged yet.  ", "warning"),
            ("Run ", "muted"),
            ("git add <files>", "info.bold"),
            (" and then ", "muted"),
            ("quill", "info.bold"),
            (" again.", "muted"),
        )
        return Panel(
            message, title=title, title_align="left",
            border_style="border", box=box.ROUNDED, padding=(1, 2),
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
        table.add_row(Text(f"… and {hidden} more", style="muted.italic"), "", "", "")

    footer = Text.assemble(
        (f" {_files(len(files))} ", "muted"),
        (f" +{diff.additions} ", "success.bold"),
        (f" -{diff.deletions} ", "error.bold"),
    )

    return Panel(
        table,
        title=title,
        title_align="left",
        subtitle=footer,
        subtitle_align="right",
        border_style="border",
        box=box.ROUNDED,
        padding=(1, 2),
    )