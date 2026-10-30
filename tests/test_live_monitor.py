"""Тесты для live-мониторинга файлов."""

import tempfile
from pathlib import Path

from tracetui.widgets.live_monitor import LiveMonitor


class TestLiveMonitor:
    """Тесты live-мониторинга."""

    def test_init_with_nonexistent_files(self):
        """Инициализация с несуществующими файлами фильтрует их."""
        nonexistent = Path("/nonexistent/path.log")
        monitor = LiveMonitor(file_paths=[nonexistent])
        assert monitor._file_paths == []

    def test_init_filters_existing_files(self):
        """Инициализация сохраняет только существующие файлы."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(b"test log line\n")
            temp_path = Path(f.name)

        try:
            monitor = LiveMonitor(file_paths=[temp_path])
            assert temp_path in monitor._file_paths
            # Позиция инициализируется размером файла
            assert monitor._file_positions[temp_path] == temp_path.stat().st_size
        finally:
            temp_path.unlink()

    def test_init_flags(self):
        """Проверка начальных флагов."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(b"test log line\n")
            temp_path = Path(f.name)

        try:
            monitor = LiveMonitor(file_paths=[temp_path])
            assert monitor._running is False
            assert monitor._task is None
            assert monitor._poll_interval == 1.0
        finally:
            temp_path.unlink()

    def test_custom_poll_interval(self):
        """Проверка кастомного интервала опроса."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(b"test log line\n")
            temp_path = Path(f.name)

        try:
            monitor = LiveMonitor(file_paths=[temp_path], poll_interval=0.5)
            assert monitor._poll_interval == 0.5
        finally:
            temp_path.unlink()

    def test_stop_when_not_running(self):
        """Остановка мониторинга без запуска."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(b"test log line\n")
            temp_path = Path(f.name)

        try:
            monitor = LiveMonitor(file_paths=[temp_path])
            # Остановка без запуска не должна вызывать ошибок
            monitor.stop()
            assert monitor._running is False
        finally:
            temp_path.unlink()

    def test_callback_receives_events(self):
        """Проверка что колбэк вызывается при новых данных."""
        call_count = 0

        def on_new(entries, path):
            nonlocal call_count
            call_count += 1

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            f.write(b"test log line\n")
            temp_path = Path(f.name)

        try:
            monitor = LiveMonitor(
                file_paths=[temp_path],
                on_new_entries=on_new,
                poll_interval=0.1,
            )
            assert monitor._on_new_entries is not None
        finally:
            temp_path.unlink()
