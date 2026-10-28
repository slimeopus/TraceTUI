"""Тесты для DetailPanel виджета."""

from tracetui.models import LogLevel, LogEntry
from tracetui.widgets.detail_panel import DetailPanel


class TestDetailPanel:
    """Тесты панели деталей."""

    def test_initial_display(self):
        """Начальное состояние — подсказка."""
        panel = DetailPanel()
        panel.on_mount()
        assert "Select a log entry" in panel.text

    def test_update_with_entry(self):
        """Обновление деталями записи."""
        panel = DetailPanel()
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Something broke",
            timestamp="2024-01-01 12:00:00",
            logger_name="app.main",
        )
        panel.update_detail(entry)
        assert "ERROR" in panel.text
        assert "Something broke" in panel.text
        assert "2024-01-01 12:00:00" in panel.text

    def test_update_with_traceback(self):
        """Отображение traceback."""
        panel = DetailPanel()
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Crash",
            traceback="Traceback (most recent call last):\n  File 'app.py', line 10",
        )
        panel.update_detail(entry)
        assert "Traceback" in panel.text
        assert "app.py" in panel.text

    def test_toggle_traceback_visible(self):
        """Traceback виден."""
        panel = DetailPanel()
        panel._show_traceback = True
        assert panel._show_traceback is True

    def test_toggle_traceback_hidden(self):
        """Traceback скрыт."""
        panel = DetailPanel()
        panel._show_traceback = False
        assert panel._show_traceback is False

    def test_toggle_traceback_action(self):
        """Переключение через action."""
        panel = DetailPanel()
        initial = panel._show_traceback
        panel.action_toggle_traceback()
        assert panel._show_traceback == (not initial)

    def test_update_none_entry(self):
        """Обновление None — возврат к подсказке."""
        panel = DetailPanel()
        panel.update_detail(None)
        assert "Select a log entry" in panel.text

        entry = LogEntry(level=LogLevel.ERROR, message="test")
        panel.update_detail(entry)
        assert "test" in panel.text

    def test_current_entry_property(self):
        """Свойство current_entry."""
        panel = DetailPanel()
        assert panel.current_entry is None

        entry = LogEntry(level=LogLevel.INFO, message="test")
        panel.update_detail(entry)
        assert panel.current_entry is entry

    def test_detail_with_tags(self):
        """Отображение тегов."""
        panel = DetailPanel()
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="error",
            tags=["исследовать", "решено"],
        )
        panel.update_detail(entry)
        assert "исследовать" in panel.text
        assert "решено" in panel.text

    def test_detail_without_optional_fields(self):
        """Минимальная запись без timestamp/logger."""
        panel = DetailPanel()
        entry = LogEntry(level=LogLevel.INFO, message="simple")
        panel.update_detail(entry)
        assert "INFO" in panel.text
        assert "simple" in panel.text
