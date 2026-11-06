"""Тесты для моделей."""

import pytest
from pathlib import Path
from datetime import datetime
from tracetui.models import LogLevel, LogEntry, LogSource


class TestLogSource:
    """Тесты для LogSource."""

    def test_log_source_creation(self):
        """Создание источника логов."""
        source = LogSource(
            name="test.log",
            path=Path("/var/log/test.log"),
        )

        assert source.name == "test.log"
        assert source.format_type == "auto"
        assert source.entry_count == 0
        assert not source.is_active
        assert not source.has_new

    def test_log_source_with_entries(self):
        """Источник с записями."""
        from tracetui.models import LogLevel

        entries = [
            LogEntry(level=LogLevel.INFO, message="Test 1"),
            LogEntry(level=LogLevel.ERROR, message="Test 2"),
        ]

        source = LogSource(
            name="test.log",
            path=Path("/var/log/test.log"),
            entries=entries,
        )

        assert source.entry_count == 2


class TestTimestampDt:
    """Тесты для LogEntry.timestamp_dt."""

    def test_timestamp_dt_loguru_format(self):
        """Конвертация timestamp в формате loguru."""
        from tracetui.parsers.log_parser import LogParser
        dt = LogParser.parse_timestamp("2024-01-15 10:30:45")
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test",
            timestamp="2024-01-15 10:30:45",
            timestamp_dt=dt,
        )
        assert entry.timestamp_dt == datetime(2024, 1, 15, 10, 30, 45)

    def test_timestamp_dt_logging_format(self):
        """Конвертация timestamp в формате logging."""
        from tracetui.parsers.log_parser import LogParser
        dt = LogParser.parse_timestamp("2024-01-15 10:30:45,123456")
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Test error",
            timestamp="2024-01-15 10:30:45,123456",
            timestamp_dt=dt,
        )
        assert entry.timestamp_dt == datetime(2024, 1, 15, 10, 30, 45, 123456)

    def test_timestamp_dt_empty(self):
        """Пустой timestamp должен вернуть None."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="No timestamp",
            timestamp_dt=None,
        )
        assert entry.timestamp_dt is None

    def test_timestamp_dt_caching(self):
        """timestamp_dt сохраняется при создании."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test",
            timestamp="2024-01-15 10:30:45",
            timestamp_dt=dt,
        )
        first_call = entry.timestamp_dt
        second_call = entry.timestamp_dt
        assert first_call is second_call
