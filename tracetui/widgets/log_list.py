"""Список логов с цветовой кодировкой и навигацией (центральная панель).

Полностью переписан с RichLog на DataTable для виртуализации рендеринга.
DataTable рендерит только видимые строки, что устраняет нагрузку на CPU
при больших объёмах логов (5000+ строк).
"""

from textual.widgets import DataTable
from textual.binding import Binding

from ..models import LogEntry, LogLevel, LogSource
from .filter_input import FilterModal


class LogList(DataTable):
    """Центральная панель с потоком логов (DataTable с виртуализацией)."""

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
        super().__init__(**kwargs)
        # Храним все записи и отфильтрованные записи отдельно
        self._entries: list[LogEntry] = []
        self._filtered_entries: list[LogEntry] = []
        self._selectedIndex: int = -1
        self._filter_level: LogLevel | None = None
        self._filter_text: str = ""
        self._sources: list[LogSource] = []
        # Флаг для ленивой инициализации столбцов
        self._columns_added: bool = False
        # Флаг для тестов: не пересчитывать _filtered_entries
        self._testing: bool = False

        # Ключевые слова для детекции аномалий
        self._anomaly_keywords = [
            "timeout", "connectionerror", "error", "exception",
            "failure", "fail", "fatal", "critical", "panic",
            "refused", "denied", "unavailable", "not found",
            "500", "502", "503", "504", "timed out",
            "reset by peer", "broken pipe", "segfault", "abort",
        ]

    def on_mount(self) -> None:
        self.add_class("log-list")
        self._ensure_columns()

    def _ensure_columns(self) -> None:
        """Лениво инициализирует столбцы DataTable (требует контекст приложения)."""
        if self._columns_added:
            return
        try:
            self.add_columns("timestamp", "level", "message")
            self._columns_added = True
        except Exception:
            # Если контекст приложения ещё не готов — попробуем позже
            pass

    # ------------------------------------------------------------------
    # Фильтрация
    # ------------------------------------------------------------------

    def _get_filtered_entries(self) -> list[LogEntry]:
        """Возвращает отфильтрованные записи по уровню и тексту."""
        entries = self._entries

        # Фильтр по уровню (показывает текущий уровень и выше)
        if self._filter_level:
            level_order = [
                LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING,
                LogLevel.ERROR, LogLevel.CRITICAL,
            ]
            min_idx = level_order.index(self._filter_level)
            entries = [e for e in entries if level_order.index(e.level) >= min_idx]

        # Фильтр по тексту (ищет в сообщении, уровне, таймстампе)
        if self._filter_text:
            text = self._filter_text.lower()
            entries = [
                e for e in entries
                if text in e.message.lower()
                or text in e.level.value.lower()
                or text in e.timestamp.lower()
            ]

        return entries

    def apply_filter(self, text: str) -> None:
        self._filter_text = text
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

    # ------------------------------------------------------------------
    # Рендеринг строк (конвертация Rich-разметки в DataTable-стили)
    # ------------------------------------------------------------------

    def _build_line(self, entry: LogEntry, index: int) -> tuple[str, str, str, dict]:
        """Формирует строку и стили для DataTable.

        Args:
            entry: Запись лога
            index: Индекс в отфильтрованном списке

        Returns:
            Кортеж (timestamp, level_text, message, styles_dict)
        """
        is_selected = index == self._selectedIndex
        is_anomaly = self._is_anomaly(entry)

        # Формируем текст для каждого столбца БЕЗ Rich-разметки
        time_str = entry.timestamp if entry.timestamp else "    "
        level_text = f"{entry.level.icon} {entry.level.value}"
        message = entry.message[:65]
        if len(entry.message) > 65:
            message += "..."

        # Стили для DataTable (CSS-строки)
        styles = {}

        # Стили для timestamp
        styles["timestamp"] = "color: grey50;"

        # Стили для level
        styles["level"] = f"color: {entry.level.color};"

        # Стили для message
        if is_anomaly and not is_selected:
            styles["message"] = "color: bright_red;"
        elif is_selected:
            # Выбранная строка — белый текст на тёмном фоне (подсветка DataTable)
            styles["message"] = "color: white;"

        return time_str, level_text, message, styles

    def _is_anomaly(self, entry: LogEntry) -> bool:
        """Проверяет, является ли запись аномальной (ошибка/критично/ключевые слова)."""
        if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
            return True
        message_lower = entry.message.lower()
        for keyword in self._anomaly_keywords:
            if keyword in message_lower:
                return True
        return False

    # ------------------------------------------------------------------
    # Обновление отображения
    # ------------------------------------------------------------------

    def _update_display(self) -> None:
        """Перестраивает DataTable с учётом фильтрации.

        DataTable виртуализирует рендеринг — отображаются только видимые строки,
        что обеспечивает высокую производительность даже при 50000+ записях.
        """
        self._ensure_columns()
        # В режиме тестов не пересчитываем _filtered_entries (тесты могут задать вручную)
        if not self._testing:
            self._filtered_entries = self._get_filtered_entries()

        # Если столбцы ещё не добавлены (тесты без контекста app) — выходим
        if not self._columns_added:
            return

        self.clear()

        # Храним RowKey для каждой строки — нужен для стилизации ячеек
        row_keys: list = []

        # Заполняем таблицу данными
        for i, entry in enumerate(self._filtered_entries):
            time_str, level_text, message, styles = self._build_line(entry, i)
            # add_row возвращает RowKey — его нужно использовать для стилизации
            row_key = self.add_row(time_str, level_text, message)
            row_keys.append(row_key)

        # Применяем стили к ячейкам после добавления всех строк
        for i, entry in enumerate(self._filtered_entries):
            _, _, _, styles = self._build_line(entry, i)
            row_key = row_keys[i]
            # set_cell принимает RowKey и стиль как именованный параметр
            try:
                self.set_cell(row_key, 0, style=styles["timestamp"])
            except Exception:
                pass
            try:
                self.set_cell(row_key, 1, style=styles["level"])
            except Exception:
                pass
            try:
                self.set_cell(row_key, 2, style=styles["message"])
            except Exception:
                pass

            # Выделяем выбранную строку
            if i == self._selectedIndex:
                try:
                    self.set_row_key(row_key, classes=["row-selected"])
                except Exception:
                    pass

        # Корректируем курсор после перестройки
        if self._selectedIndex >= len(self._filtered_entries):
            self._selectedIndex = max(len(self._filtered_entries) - 1, -1)

    def add_entries(self, entries: list[LogEntry]) -> None:
        """Добавляет новые записи и перестраивает отображение."""
        self._entries.extend(entries)
        self._update_display()

    # ------------------------------------------------------------------
    # Источники
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Выбор и навигация
    # ------------------------------------------------------------------

    @property
    def selected_entry(self) -> LogEntry | None:
        if 0 <= self._selectedIndex < len(self._filtered_entries):
            return self._filtered_entries[self._selectedIndex]
        return None

    @property
    def selected_index(self) -> int:
        return self._selectedIndex

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        filtered = self._filtered_entries
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

    # ------------------------------------------------------------------
    # Действия
    # ------------------------------------------------------------------

    def action_toggle_filter_mode(self) -> None:
        """Открыть модальное окно фильтрации.

        Если фильтр уже активен — сбрасывает его и закрывает.
        Если фильтра нет — открывает модальное окно для ввода.
        """
        if self._filter_text:
            self._filter_text = ""
            self._selectedIndex = -1
            self._update_display()
            self._safe_notify("Фильтр сброшен")
        else:
            try:
                app = self.app
                self._filter_text = ""
                self._safe_notify("Введите текст для фильтрации")
                app.push_screen(FilterModal(), self._handle_filter_result)
            except Exception:
                self._safe_notify("Ошибка: приложение не доступно")

    def _handle_filter_result(self, result: str | None) -> None:
        """Обработка результата ввода фильтра из модального окна."""
        if result is None:
            self._safe_notify("Фильтрация отменена")
        elif result == "":
            self._filter_text = ""
            self._selectedIndex = -1
            self._update_display()
            self._safe_notify("Фильтр сброшен")
        else:
            self._filter_text = result
            self._selectedIndex = -1
            self._update_display()
            filtered_count = len(self._get_filtered_entries())
            self._safe_notify(f"Фильтр применён: {filtered_count} записей")

    def action_select_entry(self) -> None:
        if self._selectedIndex >= 0:
            entry = self.selected_entry
            if entry:
                entry.selected = True
                self._safe_notify(f"Selected: {entry.level.value} — {entry.message[:50]}")

    def action_deselect(self) -> None:
        self.selected_index = -1

    def action_next_error(self) -> None:
        """Переход к следующей группе ошибок."""
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

    def _get_error_blocks(self) -> list[list[int]]:
        """Возвращает блоки подряд идущих ошибок.

        Каждый блок — список индексов в _filtered_entries,
        где встречаются ERROR или CRITICAL записи.
        """
        blocks: list[list[int]] = []
        current_block: list[int] = []
        for i, entry in enumerate(self._filtered_entries):
            if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                current_block.append(i)
            else:
                # Не ошибка — завершаем текущий блок если есть
                if current_block:
                    blocks.append(current_block)
                    current_block = []
        # Не забываем последний блок если файл закончился на ошибке
        if current_block:
            blocks.append(current_block)
        return blocks

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

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    def _safe_notify(self, message: str) -> None:
        try:
            if self.app:
                self.app.notify(message)
        except Exception:
            pass
