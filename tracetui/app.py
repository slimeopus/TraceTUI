"""Основной TUI экран TraceTUI."""

import asyncio
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer
from textual.css.query import NoMatches
from textual.theme import Theme

from .widgets.log_list import LogList
from .widgets.source_panel import SourcePanel
from .widgets.detail_panel import DetailPanel
from .models import LogSource
from .parsers.log_parser import load_log_source


class TraceTUIApp(App):
    """Главное приложение TraceTUI."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 3fr 6fr 3fr;
        grid-gutter: 1 2;
    }

    #source-panel {
        width: 100%;
        height: 95%;
        background: $surface;
        border: solid $accent;
        padding: 1;
        overflow: auto;
    }

    #log-list {
        width: 100%;
        height: 95%;
        background: $boost;
        border: solid $primary;
        padding: 1;
        overflow: auto;
    }

    #detail-panel {
        width: 100%;
        height: 95%;
        background: $surface;
        border: solid $accent;
        padding: 1;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "toggle_filter_mode", "Filter"),
        Binding("e", "next_error", "Next error"),
        Binding("t", "toggle_theme", "Theme"),
        Binding("left", "switch_source_left", "Prev source"),
        Binding("right", "switch_source_right", "Next source"),
    ]

    def __init__(self, file_paths: list[Path] | None = None, format_type: str = "auto", **kwargs):
        super().__init__(**kwargs)
        self._is_dark = True
        self._pending_sources: list[LogSource] = []
        # Пути к файлам для асинхронной загрузки
        self._file_paths: list[Path] = file_paths or []
        self._format_type: str = format_type

    def on_mount(self) -> None:
        """Инициализация приложения."""
        self._sources: list[LogSource] = []
        self.title = "TraceTUI — Log Debugger"
        self.sub_title = "↑↓ Navigate | ←→ Sources | F Filter | D Tag | E Next Error | T Theme | q Quit"

        # Регистрируем светлую тему
        self.register_theme(
            Theme(
                name="trace-light",
                primary="#1976d2",
                warning="#f57f17",
                error="#c62828",
                success="#2e7d32",
                accent="#7b1fa2",
                foreground="#1a1a1a",
                background="#f0f0f0",
                surface="#e0e0e0",
                panel="#eeeeee",
                boost="#ffffff",
                dark=False,
            )
        )
        # Принудительно регистрируем тему "textual" из built-in
        self.register_theme(
            Theme(
                name="textual",
                primary="#0072ff",
                warning="#ffaf00",
                error="#e6193C",
                success="#13a10e",
                accent="#8888fc",
                foreground="#f8f8f2",
                background="#272822",
                surface="#1f2229",
                panel="#272822",
                boost="#353b45",
                dark=True,
            )
        )

        # Откладываем загрузку до полной инициализации экрана
        self.call_later(self._load_pending_sources)
        # Запускаем асинхронную загрузку файлов
        self.call_later(self._load_sources_from_paths)

    def compose(self):
        """Создание интерфейса с тремя панелями."""
        yield Header()
        yield SourcePanel(id="source-panel")
        yield LogList(id="log-list")
        yield DetailPanel(id="detail-panel")
        yield Footer()

    def add_log_source(self, source: LogSource) -> None:
        """Добавляет источник логов (откладывается до монтирования)."""
        self._sources.append(source)
        self._pending_sources.append(source)

    async def _load_sources_from_paths(self) -> None:
        """Асинхронная загрузка файлов в фоне."""
        if not self._file_paths:
            return

        async def _parse_and_register(path: Path) -> None:
            """Парсит файл в фоне и регистрирует результат."""
            # to_thread запускает синхронную функцию в пуле потоков
            source = await asyncio.to_thread(load_log_source, path, self._format_type)
            self.call_after_refresh(self._register_source, source)

        tasks = []
        for path in self._file_paths:
            if path.exists():
                tasks.append(_parse_and_register(path))
            else:
                self.call_after_refresh(lambda p=path: self.notify(f"Файл не найден: {p}", severity="error"))

        await asyncio.gather(*tasks)

    def _load_pending_sources(self) -> None:
        """Загружаем все отложенные источники после полной инициализации."""
        for source in self._pending_sources:
            self._register_source(source)
        self._pending_sources.clear()

    def _register_source(self, source: LogSource) -> None:
        """Регистрирует источник в панелях."""
        # Добавляем в список, если ещё нет
        if source not in self._sources:
            self._sources.append(source)

        source_panel = self.query_one("#source-panel", SourcePanel)
        source_panel.add_source(source)

        log_list = self.query_one("#log-list", LogList)
        log_list.add_entries(source.entries)
        log_list.set_sources(self._sources)

        # Активируем первый источник
        if self._sources.index(source) == 0:
            source.is_active = True
            source_panel.refresh()

    def action_toggle_filter_mode(self) -> None:
        """Включить/выключить режим фильтрации."""
        log_list = self.query_one("#log-list", LogList)
        log_list.action_toggle_filter_mode()
        if log_list._filter_mode:
            self.notify("Filter mode ON — Enter text, Enter to apply, Esc to cancel")

    def action_next_error(self) -> None:
        """Переход к следующей ошибке."""
        log_list = self.query_one("#log-list", LogList)
        log_list.action_next_error()

    def action_toggle_theme(self) -> None:
        """Переключает тему (светлая/тёмная)."""
        self._is_dark = not self._is_dark
        self.theme = "trace-light" if not self._is_dark else "textual"
        self.notify("Theme: Dark" if self._is_dark else "Theme: Light")

    def action_switch_source_left(self) -> None:
        """Переключить на предыдущий источник."""
        log_list = self.query_one("#log-list", LogList)
        log_list.action_cursor_left()

    def action_switch_source_right(self) -> None:
        """Переключить на следующий источник."""
        log_list = self.query_one("#log-list", LogList)
        log_list.action_cursor_right()
