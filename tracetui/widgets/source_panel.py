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
        Binding("space", "toggle_source", "Toggle"),
        Binding("left", "select_prev", "Prev"),
        Binding("right", "select_next", "Next"),
    ]

    # Реактивное свойство
    text = reactive("", init=False)

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.sources: list[LogSource] = []
        self._selected_index: int = 0

    @staticmethod
    def _get_source_color(source_name: str) -> str:
        """Генерирует цвет из хэша имени файла (синхронизируется с LogList)."""
        colors = ["blue", "green", "yellow", "magenta", "cyan", "red", "white"]
        return colors[hash(source_name) % len(colors)]

    def on_mount(self) -> None:
        """Настройка внешнего вида панели."""
        self.add_class("source-panel")
        self._refresh_sources()

    def watch_text(self, text: str) -> None:
        """Реакция на изменение text."""
        self.update(text)

    def _get_app_merge_mode(self) -> bool:
        """Проверяет, включён ли merge mode у приложения."""
        try:
            if self.app and hasattr(self.app, "merge_mode"):
                return self.app.merge_mode  # type: ignore[no-any-return]
        except Exception:
            pass
        return False

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
                if self._get_app_merge_mode():
                    checked = "✓"
                    indicator = f"[bold bright_cyan][{checked}][/]" if i == self._selected_index else f"[dim][{checked}][/]"
                    included_marker = "✓" if source.is_included else " "
                    color = self._get_source_color(source.name)
                    new_badge = " *" if source.has_new else ""
                    lines.append(
                        f"  {indicator} [bold {color}]{source.name}[/{color}] [{included_marker}]"
                        f" [dim]({source.entry_count} entries)[/dim]"
                        f"{new_badge}"
                    )
                else:
                    # Обычный режим — показываем активный источник
                    indicator = "[bold bright_yellow]▸[/]" if source.is_active else "○"
                    new_badge = " *" if source.has_new else ""
                    lines.append(
                        f"  {indicator} [bold]{source.name}[/bold]"
                        f" [dim]({source.entry_count} entries)[/dim]"
                        f"{new_badge}"
                    )

        if self._get_app_merge_mode():
            lines.append("")
            lines.append("[dim]Space: Toggle | ←→ Select[/dim]")
        else:
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

    def action_toggle_source(self) -> None:
        """Переключает включение источника в merge mode."""
        if not self.sources or not self._get_app_merge_mode():
            return
        source = self.sources[self._selected_index]
        source.is_included = not source.is_included
        self._refresh_sources()
        # Уведомляем приложение о перестройке таймлайна
        self._notify_timeline_refresh()

    def action_select_prev(self) -> None:
        """Выбрать предыдущий источник."""
        if not self.sources:
            return
        self._selected_index = (self._selected_index - 1) % len(self.sources)
        self._refresh_sources()

    def action_select_next(self) -> None:
        """Выбрать следующий источник."""
        if not self.sources:
            return
        self._selected_index = (self._selected_index + 1) % len(self.sources)
        self._refresh_sources()

    def _notify_timeline_refresh(self) -> None:
        """Уведомляет приложение о необходимости перестроить таймлайн."""
        try:
            if self.app and self._get_app_merge_mode():
                # Запускаем асинхронно через call_later
                self.app.call_later(lambda: self.app._refresh_timeline_async())
        except Exception:
            pass
