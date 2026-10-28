"""Тесты для парсера логов."""

import pytest
from pathlib import Path
from tracetui.parsers.log_parser import LogParser
from tracetui.models import LogLevel, LogEntry


class TestLogParser:
    """Тесты для LogParser."""

    def test_detect_loguru_format(self):
        """Определение формата loguru."""
        line = "2024-01-15 10:30:45 | ERROR | module.py:42 - Something went wrong"
        assert LogParser.detect_format(line) == "loguru"

    def test_detect_logging_format(self):
        """Определение формата standard logging."""
        line = "2024-01-15 10:30:45,123 - module.name - ERROR - Something went wrong"
        assert LogParser.detect_format(line) == "logging"

    def test_detect_simple_format(self):
        """Определение простого формата."""
        line = "ERROR - Something went wrong"
        assert LogParser.detect_format(line) == "simple"

    def test_parse_loguru_line(self):
        """Парсинг строки loguru."""
        line = "2024-01-15 10:30:45 | ERROR | module.py:42 - Something went wrong"
        entry = LogParser.parse_line(line, "loguru")

        assert entry is not None
        assert entry.level == LogLevel.ERROR
        assert entry.message == "Something went wrong"
        assert entry.timestamp == "2024-01-15 10:30:45"
        assert entry.line_number == 42

    def test_parse_logging_line(self):
        """Парсинг строки standard logging."""
        line = "2024-01-15 10:30:45,123 - app.main - WARNING - Low disk space"
        entry = LogParser.parse_line(line, "logging")

        assert entry is not None
        assert entry.level == LogLevel.WARNING
        assert entry.message == "Low disk space"
        assert entry.logger_name == "app.main"

    def test_parse_simple_line(self):
        """Парсинг простой строки."""
        line = "INFO - Application started"
        entry = LogParser.parse_line(line, "simple")

        assert entry is not None
        assert entry.level == LogLevel.INFO
        assert entry.message == "Application started"

    def test_parse_empty_line(self):
        """Пустая строка должна вернуть None."""
        assert LogParser.parse_line("") is None
        assert LogParser.parse_line("   ") is None

    def test_parse_unknown_format(self):
        """Неизвестный формат должен вернуть None."""
        line = "This is not a log line"
        assert LogParser.parse_line(line, "unknown") is None

    def test_auto_detect_and_parse(self):
        """Автоопределение и парсинг."""
        loguru_line = "2024-01-15 10:30:45 | INFO | app - Started"
        entry = LogParser.parse_line(loguru_line)
        assert entry is not None
        assert entry.level == LogLevel.INFO

    def test_all_log_levels(self):
        """Тестирование всех уровней логирования."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            line = f"{level} - Test message"
            entry = LogParser.parse_line(line, "simple")
            assert entry is not None
            assert entry.level == LogLevel(level)


class TestLogLevel:
    """Тесты для LogLevel."""

    def test_level_colors(self):
        """Проверка цветов уровней."""
        assert LogLevel.ERROR.color == "red1"
        assert LogLevel.WARNING.color == "orange1"
        assert LogLevel.DEBUG.color == "grey50"
        assert LogLevel.INFO.color == "white"

    def test_level_icons(self):
        """Проверка иконок уровней."""
        assert LogLevel.ERROR.icon == "✕"
        assert LogLevel.WARNING.icon == "⚠"
        assert LogLevel.DEBUG.icon == "⚬"
        assert LogLevel.INFO.icon == "ℹ"


class TestLogEntry:
    """Тесты для LogEntry."""

    def test_log_entry_creation(self):
        """Создание записи лога."""
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Test error",
            timestamp="2024-01-15 10:30:45",
            logger_name="app.main",
        )

        assert entry.level == LogLevel.ERROR
        assert entry.message == "Test error"
        assert entry.tags == []
        assert entry.selected is False

    def test_log_entry_with_traceback(self):
        """Создание записи с traceback."""
        traceback = "Traceback (most recent call last):\n  File 'app.py', line 10\n    raise Error()"
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Something failed",
            traceback=traceback,
        )

        assert entry.traceback == traceback
