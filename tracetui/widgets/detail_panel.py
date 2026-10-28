"""Панель деталей выбранной строки (правая панель)."""

from textual.widgets import Static
from textual.binding import Binding
from textual.reactive import reactive

from ..models import LogEntry


class DetailPanel(Static):
    """Правая панель с деталями выбранной записи лога."""

    BINDINGS = [
        Binding("c", "copy_traceback", "Copy traceback"),
        Binding("e", "toggle_traceback", "Toggle traceback"),
    ]

    # Реактивное свойство
    text = reactive("", init=False)

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._current_entry: LogEntry | None = None
        self._show_traceback = True

    def on_mount(self) -> None:
        """Настройка панели."""
        self.add_class("detail-panel")
        self._update_text()

    def watch_text(self, text: str) -> None:
        """Реакция на изменение text."""
        self.update(text)

    def _update_text(self) -> None:
        """Обновляет текстовое свойство панели."""
        if not self._current_entry:
            self.text = "[dim]Select a log entry to see details[/dim]"
            return

        parts = []
        parts.append(f"[bold]{self._current_entry.level.icon} {self._current_entry.level.value}[/bold]")

        if self._current_entry.timestamp:
            parts.append(f"[dim]Timestamp:[/dim] {self._current_entry.timestamp}")

        if self._current_entry.logger_name:
            parts.append(f"[dim]Logger:[/dim] {self._current_entry.logger_name}")

        if self._current_entry.file_path:
            line_info = self._current_entry.file_path
            if self._current_entry.line_number:
                line_info += f":{self._current_entry.line_number}"
            parts.append(f"[dim]File:[/dim] {line_info}")

        parts.append("")
        parts.append(f"[bold]Message:[/bold]")
        parts.append(self._current_entry.message)

        if self._current_entry.tags:
            tags_str = ", ".join(self._current_entry.tags)
            parts.append(f"[dim]Tags:[/dim] {tags_str}")

        if self._current_entry.traceback:
            parts.append("")
            parts.append(f"[dim]Traceback:[/dim]")
            if self._show_traceback:
                parts.append(f"[{self._current_entry.level.color}]{self._current_entry.traceback}[/]")

        self.text = "\n".join(parts)

    def update_detail(self, entry: LogEntry | None) -> None:
        """Обновляет детали выбранной записи."""
        self._current_entry = entry
        self._update_text()

    def toggle_traceback(self) -> None:
        """Переключает отображение traceback."""
        self._show_traceback = not self._show_traceback
        if self._current_entry:
            self._update_text()

    def action_toggle_traceback(self) -> None:
        """Переключает отображение traceback."""
        self.toggle_traceback()

    def action_copy_traceback(self) -> None:
        """Копирует traceback в буфер обмена."""
        if self._current_entry and self._current_entry.traceback:
            try:
                self.app.write_clipboard(self._current_entry.traceback)  # type: ignore[attr-defined]
                self._safe_notify("Traceback copied to clipboard")
            except Exception:
                pass

    def _safe_notify(self, message: str) -> None:
        """Безопасное уведомление."""
        try:
            self.app.notify(message)
        except Exception:
            pass

    @property
    def current_entry(self) -> LogEntry | None:
        """Возвращает текущую выбранную запись."""
        return self._current_entry
