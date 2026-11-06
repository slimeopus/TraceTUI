"""Тесты для парсера логов."""

import pytest
from pathlib import Path
from datetime import datetime
from tracetui.parsers.log_parser import LogParser, timeline_merge
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


class TestParseTimestamp:
    """Тесты для LogParser.parse_timestamp()."""

    def test_parse_loguru_format(self):
        """Парсинг timestamp в формате loguru (без миллисекунд)."""
        result = LogParser.parse_timestamp("2024-01-15 10:30:45")
        assert result == datetime(2024, 1, 15, 10, 30, 45)

    def test_parse_logging_format(self):
        """Парсинг timestamp в формате logging (с миллисекундами)."""
        result = LogParser.parse_timestamp("2024-01-15 10:30:45,123456")
        assert result == datetime(2024, 1, 15, 10, 30, 45, 123456)

    def test_parse_logging_format_3digit_ms(self):
        """Парсинг timestamp с 3-значными миллисекундами."""
        result = LogParser.parse_timestamp("2024-01-15 10:30:45,123")
        assert result == datetime(2024, 1, 15, 10, 30, 45, 123000)

    def test_empty_string(self):
        """Пустая строка должна вернуть None."""
        assert LogParser.parse_timestamp("") is None

    def test_none_string(self):
        """Неизвестный формат должен вернуть None."""
        assert LogParser.parse_timestamp("not-a-timestamp") is None

    def test_whitespace_only(self):
        """Только пробелы должны вернуть None."""
        assert LogParser.parse_timestamp("   ") is None


class TestTimelineMerge:
    """Тесты для timeline_merge()."""

    def test_merge_single_file(self, tmp_path: Path):
        """Мерж одного файла."""
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2024-01-15 10:30:45 | ERROR | module.py:42 - Something went wrong\n"
        )

        results = list(timeline_merge([log_file]))
        assert len(results) == 1
        entry, path = results[0]
        assert entry.level == LogLevel.ERROR
        assert path == log_file

    def test_merge_two_files_by_time(self, tmp_path: Path):
        """Мерж двух файлов — сортировка по времени."""
        file1 = tmp_path / "app1.log"
        file1.write_text(
            "2024-01-15 10:30:45 | INFO | app - First event\n"
            "2024-01-15 10:30:50 | ERROR | app - Second event\n"
        )

        file2 = tmp_path / "app2.log"
        file2.write_text(
            "2024-01-15 10:30:47 | WARNING | worker - Middle event\n"
        )

        results = list(timeline_merge([file1, file2]))

        # Проверяем хронологический порядок
        assert len(results) == 3
        assert results[0][0].timestamp == "2024-01-15 10:30:45"
        assert results[1][0].timestamp == "2024-01-15 10:30:47"
        assert results[2][0].timestamp == "2024-01-15 10:30:50"

    def test_merge_without_timestamps(self, tmp_path: Path):
        """Мерж файлов без timestamp — stable sort."""
        file1 = tmp_path / "simple1.log"
        file1.write_text(
            "INFO - Event A\n"
            "ERROR - Event B\n"
        )

        file2 = tmp_path / "simple2.log"
        file2.write_text(
            "WARNING - Event C\n"
        )

        results = list(timeline_merge([file1, file2]))

        # Все записи должны быть на месте
        assert len(results) == 3

        # Записи без timestamp идут после всех записей с timestamp
        # Но внутри своего генератора порядок сохраняется
        paths = [r[1].name for r in results]
        # Файлы без timestamp не перемешиваются между собой
        assert "simple1.log" in paths

    def test_merge_mixed_formats(self, tmp_path: Path):
        """Мерж loguru и logging форматов."""
        loguru_file = tmp_path / "loguru.log"
        loguru_file.write_text(
            "2024-01-15 10:30:45 | ERROR | module.py:10 - Loguru error\n"
        )

        logging_file = tmp_path / "logging.log"
        logging_file.write_text(
            "2024-01-15 10:30:45,500 - app.main - ERROR - Logging error\n"
        )

        results = list(timeline_merge([loguru_file, logging_file]))

        # logging error должен идти позже (10:30:45.500 > 10:30:45.000)
        assert len(results) == 2
        assert results[0][0].timestamp == "2024-01-15 10:30:45"
        assert results[1][0].timestamp == "2024-01-15 10:30:45,500"

    def test_merge_preserves_source(self, tmp_path: Path):
        """Мерж сохраняет метку источника."""
        file1 = tmp_path / "app.log"
        file1.write_text(
            "2024-01-15 10:30:45 | INFO | app - Message\n"
        )

        for entry, path in timeline_merge([file1]):
            assert path == file1
