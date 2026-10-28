"""Список логов с цветовой кодировкой и навигацией (центральная панель)."""

from textual.widgets import RichLog
from textual.binding import Binding

from ..models import LogEntry, LogLevel, LogSource


class LogList(RichLog):
    """Центральная панель с потоком логов."""

    BINDINGS = [
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
        Binding("enter", "select_entry", "Select"),
        Binding("escape", "deselect", "Deselect"),
        Binding("f", "toggle_filter_mode", "Filter"),
        Binding("e", "next_error", "Next error"),
        Binding("d", "add_tag", "Tag"),
    ]

    def __init__(self, **kwargs):
        super().__init__(markup=True, wrap=True, **kwargs)
        self._entries: list[LogEntry] = []
        self._selectedIndex: int = -1
        self._filter_level: LogLevel | None = None
        self._filter_text: str = ""
        self._sources: list[LogSource] = []
        self._filter_mode = False

        self._anomaly_keywords = [
            "timeout", "connectionerror", "error", "exception",
            "failure", "fail", "fatal", "critical", "panic",
            "refused", "denied", "unavailable", "not found",
            "500", "502", "503", "504", "timed out",
            "reset by peer", "broken pipe", "segfault", "abort",
        ]

    def on_mount(self) -> None:
        self.add_class("log-list")

    def _build_lines(self) -> list[str]:
        """Возвращает строки для отображения (простая строковая логика)."""
        entries = self._get_filtered_entries()
        lines = []

        if not entries:
            return ["[dim]No logs loaded. Open a log file to begin.[/dim]"]

        anomaly_count = sum(1 for e in entries if self._is_anomaly(e))
        lines.append(
            f"[bold]Logs ({len(entries)} entries)[/bold]  |  [bright_red]{anomaly_count} anomalies[/bright_red]"
        )
        lines.append("")

        for i, entry in enumerate(entries):
            if i == self._selectedIndex:
                prefix = "▸ "
            else:
                prefix = "  "

            color = entry.level.color
            icon = entry.level.icon
            is_anomaly = self._is_anomaly(entry)

            time_str = f"[dim]{entry.timestamp}[/dim]" if entry.timestamp else "[dim]    [/dim]"
            level_str = f"[{color}]{icon} {entry.level.value:<8}[/]"
            message = entry.message[:65]
            if len(entry.message) > 65:
                message += "..."

            tag_str = ""
            if entry.tags:
                tag_parts = [f"[bright_yellow]{t}[/]" for t in entry.tags]
                tag_str = "  " + " ".join(tag_parts)

            anomaly_marker = " [bright_red]\\[!\\][/]" if is_anomaly else ""

            if is_anomaly and i != self._selectedIndex:
                line = f"[bright_red]{prefix}{time_str}  {level_str}  {message}{tag_str}{anomaly_marker}[/]"
            elif is_anomaly and i == self._selectedIndex:
                line = f"{prefix}{time_str}  {level_str}  {message}{tag_str}{anomaly_marker}"
            else:
                line = f"{prefix}{time_str}  {level_str}  {message}{tag_str}"

            lines.append(line)

        lines.append("")
        footer = "F Filter  E Next error  D Tag  ↑↓ Navigate  Enter Select  ←→ Sources"
        if self._filter_mode:
            footer = "[bold bright_yellow]FILTER MODE:[/bold bright_yellow] " + footer
        lines.append(f"[dim]{footer}[/dim]")

        return lines

    def _is_anomaly(self, entry: LogEntry) -> bool:
        if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            return True
        message_lower = entry.message.lower()
        for keyword in self._anomaly_keywords:
            if keyword in message_lower:
                return True
        return False

    def _update_display(self) -> None:
        lines = self._build_lines()
        self.clear()
        for line in lines:
            self.write(line)

    def add_entries(self, entries: list[LogEntry]) -> None:
        self._entries.extend(entries)
        self._update_display()

    def set_sources(self, sources: list[LogSource]) -> None:
        self._sources = sources

    @property
    def sources(self) -> list[LogSource]:
        return self._sources

    @property
    def current_source_index(self) -> int:
        if not self._sources:
            return -1
        for i, source in enumerate(self._sources):
            if source.is_active:
                return i
        return len(self._sources) - 1

    @current_source_index.setter
    def current_source_index(self, value: int) -> None:
        if not self._sources:
            return
        for source in self._sources:
            source.is_active = False
        index = max(0, min(value, len(self._sources) - 1))
        self._sources[index].is_active = True
        self._entries = list(self._sources[index].entries)
        self._selectedIndex = -1
        self._notify_source_panel()
        self._update_display()

    def _notify_source_panel(self) -> None:
        try:
            if not self.app or not self.is_mounted:
                return
            from .source_panel import SourcePanel as SP
            app = self.app
            source_panel = app.query_one("#source-panel", SP)
            source_panel._refresh_sources()
        except Exception:
            pass

    def _notify_detail_panel(self) -> None:
        try:
            if not self.app or not self.is_mounted:
                return
            from .detail_panel import DetailPanel as DP
            app = self.app
            entry = self.selected_entry
            if entry:
                detail_panel = app.query_one("#detail-panel", DP)
                detail_panel.update_detail(entry)
        except Exception:
            pass

    def _get_error_blocks(self) -> list[list[int]]:
        blocks = []
        current_block = []
        filtered = self._get_filtered_entries()
        for i, entry in enumerate(filtered):
            if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                if current_block:
                    blocks.append(current_block)
                current_block = [i]
            elif current_block:
                current_block.append(i)
        if current_block:
            blocks.append(current_block)
        return blocks

    def _get_filtered_entries(self) -> list[LogEntry]:
        entries = self._entries
        if self._filter_level:
            level_order = [
                LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING,
                LogLevel.ERROR, LogLevel.CRITICAL,
            ]
            min_idx = level_order.index(self._filter_level)
            entries = [e for e in entries if level_order.index(e.level) >= min_idx]
        if self._filter_text:
            text = self._filter_text.lower()
            entries = [
                e for e in entries
                if text in e.message.lower()
                or text in e.level.value.lower()
                or text in e.timestamp.lower()
            ]
        return entries

    @property
    def selected_entry(self) -> LogEntry | None:
        if 0 <= self._selectedIndex < len(self._get_filtered_entries()):
            return self._get_filtered_entries()[self._selectedIndex]
        return None

    @property
    def selected_index(self) -> int:
        return self._selectedIndex

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        filtered = self._get_filtered_entries()
        if value < 0:
            self._selectedIndex = -1
        elif value >= len(filtered):
            self._selectedIndex = len(filtered) - 1
        else:
            self._selectedIndex = value
        if self._selectedIndex >= 0:
            self._notify_detail_panel()
        self._update_display()

    def action_cursor_up(self) -> None:
        self.selected_index = self._selectedIndex - 1

    def action_cursor_down(self) -> None:
        self.selected_index = self._selectedIndex + 1

    def action_cursor_left(self) -> None:
        if self._sources:
            current = self.current_source_index
            self.current_source_index = current - 1
            self._safe_notify(f"Source: {self._sources[max(0, current - 1)].name}")

    def action_cursor_right(self) -> None:
        if self._sources:
            current = self.current_source_index
            self.current_source_index = current + 1
            self._safe_notify(f"Source: {self._sources[min(current + 1, len(self._sources) - 1)].name}")

    def _safe_notify(self, message: str) -> None:
        try:
            if self.app:
                self.app.notify(message)
        except Exception:
            pass

    def action_select_entry(self) -> None:
        if self._selectedIndex >= 0:
            entry = self.selected_entry
            if entry:
                entry.selected = True
                self._safe_notify(f"Selected: {entry.level.value} — {entry.message[:50]}")

    def action_deselect(self) -> None:
        self.selected_index = -1

    def action_toggle_filter_mode(self) -> None:
        self._filter_mode = not self._filter_mode
        if not self._filter_mode and self._filter_text:
            self._filter_text = ""
            self._selectedIndex = -1
            self._update_display()
        elif self._filter_mode:
            self._selectedIndex = -1
            self._update_display()

    def apply_filter(self, text: str) -> None:
        self._filter_text = text
        self._filter_mode = False
        self._selectedIndex = -1
        self._update_display()

    def set_level_filter(self, level: LogLevel | None) -> None:
        self._filter_level = level
        self._selectedIndex = -1
        self._update_display()

    def set_text_filter(self, text: str) -> None:
        self._filter_text = text
        self._selectedIndex = -1
        self._update_display()

    def action_next_error(self) -> None:
        filtered = self._get_filtered_entries()
        error_blocks = self._get_error_blocks()
        if not error_blocks:
            self._safe_notify("No errors found")
            return
        current_block_start = None
        if self._selectedIndex >= 0:
            for block in error_blocks:
                if self._selectedIndex in block:
                    current_block_start = block[0]
                    break
            if current_block_start is None:
                current_block_start = self._selectedIndex
        next_block = None
        for block in error_blocks:
            if current_block_start is None or block[0] > current_block_start:
                next_block = block
                break
        if next_block:
            self.selected_index = next_block[0]
            error_entry = filtered[next_block[0]]
            self._safe_notify(f"Error: {error_entry.message[:50]}")
        else:
            self.selected_index = error_blocks[-1][0]
            self._safe_notify("At last error")

    def action_add_tag(self) -> None:
        """Тоггл тега 'исследовать' — добавляет или убирает."""
        self._toggle_tag("исследовать")

    def _toggle_tag(self, tag: str) -> None:
        """Добавляет тег, если его нет, или убирает, если он есть."""
        entry = self.selected_entry
        if not entry:
            self._safe_notify("No entry selected")
            return
        if tag in entry.tags:
            entry.tags.remove(tag)
            self._safe_notify(f"Tag '{tag}' removed")
        else:
            entry.tags.append(tag)
            self._safe_notify(f"Tag '{tag}' added")
        self._update_display()
        self._notify_detail_panel()

    def _apply_tag(self, tag: str) -> None:
        """Применяет тег к выбранной записи (для UI и тестов)."""
        if not tag:
            return
        entry = self.selected_entry
        if entry:
            if tag not in entry.tags:
                entry.tags.append(tag)
            self._update_display()
            self._notify_detail_panel()
            self._safe_notify(f"Tag '{tag}' added")

    def add_tag(self, tag: str) -> None:
        """Добавляет тег к выбранной записи (для вызова из кода/тестов)."""
        self._apply_tag(tag)
