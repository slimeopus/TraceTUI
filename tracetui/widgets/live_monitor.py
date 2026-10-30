"""Фоновый мониторинг изменений файлов логов (tail -f).

Отслеживает изменение размера файлов и автоматически
дочитывает новые строки, обновляя источники логов.
"""

import asyncio
import logging
from pathlib import Path
from typing import Callable

from textual.widgets import RichLog

from ..parsers.log_parser import LogParser

logger = logging.getLogger(__name__)


class LiveMonitor:
    """Фоновый мониторинг файлов логов в реальном времени.

    Работает как асинхронный воркер, который:
    - Периодически проверяет размер файлов
    - Дочитывает новые строки при изменении
    - Парсит новые записи и добавляет их в LogList
    """

    def __init__(
        self,
        file_paths: list[Path],
        format_type: str = "auto",
        on_new_entries: Callable[[list, Path], None] | None = None,
        poll_interval: float = 1.0,
    ):
        """Инициализация мониторинга.

        Args:
            file_paths: Список путей к файлам для мониторинга
            format_type: Тип формата логов (auto, loguru, logging, simple)
            on_new_entries: Колбэк, вызываемый при появлении новых записей.
                           Принимает (entries, file_path).
            poll_interval: Интервал проверки в секундах
        """
        self._file_paths = [p for p in file_paths if p.exists()]
        self._format_type = format_type
        self._on_new_entries = on_new_entries
        self._poll_interval = poll_interval
        # Текущие позиции в файлах (size на момент последней проверки)
        self._file_positions: dict[Path, int] = {}
        for path in self._file_paths:
            try:
                self._file_positions[path] = path.stat().st_size
            except OSError:
                self._file_positions[path] = 0
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Запуск мониторинга в фоне."""
        if self._running:
            logger.warning("Мониторинг уже запущен")
            return
        self._running = True
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._monitor_loop())
        logger.info("Live-мониторинг запущен для %d файлов", len(self._file_paths))

    def stop(self) -> None:
        """Остановка мониторинга."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Мониторинг остановлен")

    async def _monitor_loop(self) -> None:
        """Основной цикл мониторинга."""
        while self._running:
            try:
                await self._check_files()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Ошибка в мониторинге: %s", e, exc_info=True)
            await asyncio.sleep(self._poll_interval)

    async def _check_files(self) -> None:
        """Проверить все файлы на наличие новых данных."""
        for path in list(self._file_paths):
            await self._check_single_file(path)

    async def _check_single_file(self, path: Path) -> None:
        """Проверить один файл на наличие новых данных.

        Работает асинхронно в пуле потоков для предотвращения блокировки.
        """
        try:
            current_size = path.stat().st_size
            last_position = self._file_positions.get(path, 0)

            if current_size > last_position:
                # Файл увеличился — дочитываем новые строки
                new_lines = await self._read_new_lines(path, last_position, current_size)

                if new_lines:
                    # Парсим новые строки
                    new_entries = await self._parse_new_lines(new_lines, path)

                    if new_entries and self._on_new_entries:
                        # Вызываем колбэк для обновления UI
                        self._on_new_entries(new_entries, path)

                    # Обновляем позицию
                    self._file_positions[path] = current_size

        except (OSError, IOError) as e:
            logger.warning("Не удалось проверить файл %s: %s", path, e)

    async def _read_new_lines(
        self, path: Path, start_pos: int, end_pos: int
    ) -> list[str]:
        """Прочитать новые строки из файла.

        Args:
            path: Путь к файлу
            start_pos: Позиция начала новых данных
            end_pos: Позиция конца (текущий размер)

        Returns:
            Список новых строк
        """
        loop = asyncio.get_event_loop()

        def _read() -> list[str]:
            """Синхронное чтение новых строк из файла."""
            new_content = ""
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(start_pos)
                    new_content = f.read(end_pos - start_pos)
            except (OSError, IOError) as e:
                logger.warning("Ошибка чтения %s: %s", path, e)
                return []

            # Разбиваем на строки, но последнюю строку оставляем
            # если она не завершена (нет переноса строки в конце)
            lines = new_content.splitlines(keepends=False)

            # Проверяем, что файл действительно закончился на новой строке
            try:
                with open(path, "rb") as f:
                    f.seek(end_pos - 1)
                    last_byte = f.read(1)
                    # Если последний байт не перенос строки, убираем последнюю строку
                    # (она неполная)
                    if last_byte not in (b"\n", b"\r") and lines:
                        lines.pop()
            except (OSError, IOError):
                pass

            return lines

        return await loop.run_in_executor(None, _read)

    async def _parse_new_lines(self, lines: list[str], path: Path) -> list:
        """Парсит новые строки в LogEntry.

        Args:
            lines: Список новых строк
            path: Путь к файлу

        Returns:
            Список распарсенных LogEntry
        """
        loop = asyncio.get_event_loop()

        def _parse() -> list:
            """Синхронный парсинг строк."""
            entries = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = LogParser.parse_line(line, self._format_type)
                    if entry:
                        entries.append(entry)
                except Exception as e:
                    logger.debug("Ошибка парсинга строки в %s: %s — %s", path, line[:50], e)
            return entries

        return await loop.run_in_executor(None, _parse)
