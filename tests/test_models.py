"""Тесты для моделей."""

import pytest
from pathlib import Path
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
