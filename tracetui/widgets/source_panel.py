"""Панель источников логов (левая панель)."""

from pathlib import Path
from textual.containers import Container
from textual.widgets import Static, Footer
from textual.binding import Binding
from textual.reactive import reactive

from ..models import LogSource


class SourcePanel(Static):
    """Левая панель со списком источников/файлов логов."""

    BINDINGS = [
        Binding("escape", "deselect_all", "Deselect all"),
    ]

    # Реактивное свойство
    text = reactive("", init=False)

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.sources: list[LogSource] = []

    def on_mount(self) -> None:
        """Настройка внешнего вида панели."""
        self.add_class("source-panel")
        self._refresh_sources()

    def watch_text(self, text: str) -> None:
        """Реакция на изменение text."""
        self.update(text)

    def _refresh_sources(self) -> None:
        """Обновляет текстовое свойство панели."""
        lines = []
        lines.append("[bold]Sources:[/bold]")
        lines.append("")

        if not self.sources:
            lines.append("  [dim]No sources loaded.[/dim]")
            lines.append("  [dim]Use --file argument or drop files.[/dim]")
        else:
            for i, source in enumerate(self.sources):
                indicator = "[bold bright_yellow]▸[/]" if source.is_active else "○"
                new_badge = " *" if source.has_new else ""
                lines.append(
                    f"  {indicator} [bold]{source.name}[/bold]"
                    f" [dim]({source.entry_count} entries)[/dim]"
                    f"{new_badge}"
                )

        lines.append("")
        lines.append("[dim]←→ Switch sources[/dim]")

        self.text = "\n".join(lines)

    def add_source(self, source: LogSource) -> None:
        """Добавляет источник в панель."""
        self.sources.append(source)
        self._refresh_sources()

    def action_deselect_all(self) -> None:
        """Снимает активность со всех источников."""
        for source in self.sources:
            source.is_active = False
        self._refresh_sources()
