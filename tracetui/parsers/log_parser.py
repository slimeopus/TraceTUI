"""Парсеры для различных форматов логов."""

import re
from pathlib import Path
from typing import Iterator

from ..models import LogEntry, LogSource, LogLevel


class LogParser:
    """Базовый парсер логов с автоопределением формата."""

    # Паттерн для loguru: 2024-01-15 10:30:45 | LEVEL | module.py:42 - message
    LOGURU_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[\.,\d]*)\s*\|\s*"
        r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|\s*"
        r"(?P<source>[^:]+?)(?::(?P<line>\d+))?\s*\-\s*"
        r"(?P<message>.+)"
    )

    # Паттерн для logging: 2024-01-15 10:30:45,123 - module.name - LEVEL - message
    LOGGING_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*"
        r"(?P<logger>[^:]+?)\s*-\s*"
        r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*-\s*"
        r"(?P<message>.+)"
    )

    # Паттерн с простым уровнем
    SIMPLE_PATTERN = re.compile(
        r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\-\s*(?P<message>.+)"
    )

    @staticmethod
    def detect_format(line: str) -> str:
        """Определяет формат лога по первой строке."""
        if LogParser.LOGURU_PATTERN.match(line):
            return "loguru"
        if LogParser.LOGGING_PATTERN.match(line):
            return "logging"
        if LogParser.SIMPLE_PATTERN.match(line):
            return "simple"
        return "unknown"

    @staticmethod
    def parse_line(line: str, format_type: str = "auto") -> LogEntry | None:
        """Парсит одну строку лога."""
        line = line.strip()
        if not line:
            return None

        # Auto-detect
        if format_type == "auto":
            format_type = LogParser.detect_format(line)

        parsers = {
            "loguru": LogParser._parse_loguru,
            "logging": LogParser._parse_logging,
            "simple": LogParser._parse_simple,
        }

        parser = parsers.get(format_type)
        if not parser:
            return None

        return parser(line)

    @classmethod
    def _parse_loguru(cls, line: str) -> LogEntry | None:
        """Парсит строку в формате loguru."""
        match = cls.LOGURU_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()
        level = LogLevel[data["level"]]
        source = data["source"] or ""

        traceback = ""
        message = data["message"]

        return LogEntry(
            level=level,
            message=message,
            timestamp=data["timestamp"],
            logger_name=source.split(".")[-1] if "." in source else source,
            file_path=source,
            line_number=int(data["line"]) if data.get("line") else 0,
            traceback=traceback,
        )

    @classmethod
    def _parse_logging(cls, line: str) -> LogEntry | None:
        """Парсит строку в формате standard logging."""
        match = cls.LOGGING_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()
        level = LogLevel[data["level"]]

        return LogEntry(
            level=level,
            message=data["message"],
            timestamp=data["timestamp"],
            logger_name=data["logger"],
        )

    @classmethod
    def _parse_simple(cls, line: str) -> LogEntry | None:
        """Парсит строку с простым форматом."""
        match = cls.SIMPLE_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()
        level = LogLevel[data["level"]]

        return LogEntry(
            level=level,
            message=data["message"],
        )

    @classmethod
    def _is_new_log_line(cls, line: str, format_type: str) -> bool:
        """Проверяет, является ли строкой новой записи лога."""
        stripped = line.strip()
        if not stripped:
            return False
        # Если формат уже известен — проверяем по конкретному паттерну
        if format_type != "auto":
            pattern = {
                "loguru": cls.LOGURU_PATTERN,
                "logging": cls.LOGGING_PATTERN,
                "simple": cls.SIMPLE_PATTERN,
            }.get(format_type)
            if pattern and pattern.match(stripped):
                return True
            return False
        # Auto-режим: проверяем по всем паттернам
        return bool(cls.detect_format(stripped) != "unknown")

    @classmethod
    def parse_file(cls, path: Path, format_type: str = "auto") -> Iterator[LogEntry]:
        """Парсит файл логов построчно, собирая многострочные traceback."""
        # 1. Определяем формат по первыми строкам
        if format_type == "auto":
            detected = False
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    fmt = cls.detect_format(line)
                    if fmt != "unknown":
                        format_type = fmt
                        detected = True
                        break
            # Фиксируем формат — если не определили ни один из трёх,
            # ставим "simple" чтобы не гонять detect_format() на каждую строку
            if not detected:
                format_type = "simple"

        # 2. Буферизация: накапливаем continuation lines до новой записи лога
        current_entry: LogEntry | None = None
        continuation_buffer: list[str] = []

        def flush_buffer() -> None:
            """Отдаёт накопленный entry с собранным traceback."""
            nonlocal current_entry, continuation_buffer
            if current_entry is not None:
                if continuation_buffer:
                    # Собираем traceback из буфера
                    tb_lines = []
                    for cline in continuation_buffer:
                        stripped = cline.rstrip()
                        if stripped:  # пропускаем полностью пустые строки
                            tb_lines.append(stripped)
                    if tb_lines:
                        current_entry.traceback = "\n".join(tb_lines)
                yield current_entry
            current_entry = None
            continuation_buffer = []

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                # Пустые строки — тоже continuation (разделители traceback)
                if not stripped:
                    continuation_buffer.append(line)
                    continue

                if cls._is_new_log_line(stripped, format_type):
                    # Новая запись — сначала отдаём предыдущую
                    if current_entry is not None:
                        yield from flush_buffer()
                    # Начинаем новый entry
                    current_entry = cls.parse_line(stripped, format_type)
                    continuation_buffer = []
                else:
                    # Continuation line (traceback, stack trace, и т.д.)
                    if current_entry is not None:
                        continuation_buffer.append(line)
                    # Если entry ещё нет — пропускаем сиротские строки

        # Финальная флущение последнего entry
        if current_entry is not None:
            yield from flush_buffer()

    @classmethod
    def parse_lines(
        cls,
        lines: list[str],
        format_type: str = "auto",
        partial_entry: LogEntry | None = None,
        partial_buffer: list[str] | None = None,
    ) -> tuple[list[LogEntry], LogEntry | None, list[str], str]:
        """Потоковый парсинг списка строк с сохранением состояния незавершённого traceback.

        Этот метод позволяет корректно обрабатывать новые строки, которые могут
        оборваться посередине многострочного traceback.

        Args:
            lines: Список новых строк для парсинга
            format_type: Тип формата логов
            partial_entry: Не завершённый LogEntry из предыдущей порции
            partial_buffer: Накопленные continuation lines из предыдущей порции

        Returns:
            Кортеж из:
                - list[LogEntry]: Список полностью распарсенных записей
                - LogEntry | None: Не завершённый entry (если есть)
                - list[str]: Накопленные continuation lines для незавершённого entry
                - str: Текущий формат (если был auto-detect)
        """
        # Инициализируем состояние
        if partial_entry is None:
            current_entry: LogEntry | None = None
            continuation_buffer: list[str] = []
        else:
            current_entry = partial_entry
            continuation_buffer = partial_buffer if partial_buffer is not None else []

        # Определяем формат, если auto
        if format_type == "auto":
            # Пробуем определить формат по первым непустым строкам
            for line in lines:
                stripped = line.strip()
                if stripped:
                    detected_fmt = cls.detect_format(stripped)
                    if detected_fmt != "unknown":
                        format_type = detected_fmt
                    break
            else:
                format_type = "simple"

        completed_entries: list[LogEntry] = []

        for line in lines:
            stripped = line.strip()
            # Пустые строки — тоже continuation (разделители traceback)
            if not stripped:
                continuation_buffer.append(line)
                continue

            if cls._is_new_log_line(stripped, format_type):
                # Новая запись — сначала отдаём предыдущую, если она есть
                if current_entry is not None:
                    # Формируем traceback из буфера
                    if continuation_buffer:
                        tb_lines = []
                        for cline in continuation_buffer:
                            s_line = cline.rstrip()
                            if s_line:
                                tb_lines.append(s_line)
                        if tb_lines:
                            current_entry.traceback = "\n".join(tb_lines)
                    completed_entries.append(current_entry)
                    current_entry = None
                    continuation_buffer = []

                # Начинаем новый entry
                current_entry = cls.parse_line(stripped, format_type)
                continuation_buffer = []
            else:
                # Continuation line (traceback, stack trace, и т.д.)
                if current_entry is not None:
                    continuation_buffer.append(line)
                # Если entry ещё нет — пропускаем сиротские строки

        # Возвращаем завершённые записи и состояние для незавершённого entry
        return completed_entries, current_entry, continuation_buffer, format_type


def load_log_source(path: Path, format_type: str = "auto") -> LogSource:
    """Загружает источник логов из файла."""
    source = LogSource(
        name=path.name,
        path=path,
        format_type=format_type if format_type != "auto" else "auto",
    )

    entries = list(LogParser.parse_file(path, format_type))
    source.entries = entries

    return source
