"""Тесты для LogList виджета."""

from unittest.mock import MagicMock, patch, PropertyMock
from tracetui.models import LogLevel, LogEntry
from tracetui.widgets.log_list import LogList


class MockApp:
    """Mock Textual App."""
    def notify(self, message):
        pass


class TestLogListSelection:
    """Тесты выбора записей."""

    def test_selected_entry_returns_none_when_no_entries(self):
        """Пустой список — нет выбранной записи."""
        log_list = LogList()
        assert log_list.selected_entry is None

    def test_selected_entry_returns_none_when_negative_index(self):
        """Отрицательный индекс — нет выбранной записи."""
        log_list = LogList()
        entries = [LogEntry(level=LogLevel.INFO, message="test")]
        log_list.add_entries(entries)
        assert log_list.selected_index == -1
        assert log_list.selected_entry is None

    def test_selected_entry_returns_entry_at_index(self):
        """Выбор по индексу."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="first"),
            LogEntry(level=LogLevel.ERROR, message="second"),
            LogEntry(level=LogLevel.DEBUG, message="third"),
        ]
        log_list.add_entries(entries)

        log_list.selected_index = 1
        assert log_list.selected_entry is not None
        assert log_list.selected_entry.message == "second"
        assert log_list.selected_entry.level == LogLevel.ERROR

    def test_selected_entry_out_of_bounds(self):
        """Индекс за пределами диапазона."""
        log_list = LogList()
        entries = [LogEntry(level=LogLevel.INFO, message="test")]
        log_list.add_entries(entries)

        log_list.selected_index = 100
        assert log_list.selected_index == 0

        log_list.selected_index = -5
        assert log_list.selected_index == -1


class TestLogListNavigation:
    """Тесты навигации."""

    def test_cursor_down_increases_index(self):
        """Стрелка вниз увеличивает индекс."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message=f"msg{i}")
            for i in range(5)
        ]
        log_list.add_entries(entries)
        log_list.selected_index = 0
        log_list.action_cursor_down()
        assert log_list.selected_index == 1
        log_list.action_cursor_down()
        log_list.action_cursor_down()
        assert log_list.selected_index == 3

    def test_cursor_up_decreases_index(self):
        """Стрелка вверх уменьшает индекс."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message=f"msg{i}")
            for i in range(5)
        ]
        log_list.add_entries(entries)
        log_list.selected_index = 3
        log_list.action_cursor_up()
        assert log_list.selected_index == 2
        log_list.action_cursor_up()
        assert log_list.selected_index == 1

    def test_cursor_up_from_negative(self):
        """Вверх от отрицательного индекса — остаётся отрицательным."""
        log_list = LogList()
        log_list.add_entries([
            LogEntry(level=LogLevel.INFO, message="test")
        ])
        log_list.selected_index = -1
        log_list.action_cursor_up()
        assert log_list.selected_index == -1

    def test_cursor_down_bounds(self):
        """Вниз у последнего элемента — не выходит за границы."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message=f"msg{i}")
            for i in range(3)
        ]
        log_list.add_entries(entries)
        log_list.selected_index = 2
        log_list.action_cursor_down()
        assert log_list.selected_index == 2


class TestLogListFiltering:
    """Тесты фильтрации."""

    def test_level_filter(self):
        """Фильтр по уровню."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.DEBUG, message="debug1"),
            LogEntry(level=LogLevel.INFO, message="info1"),
            LogEntry(level=LogLevel.WARNING, message="warn1"),
            LogEntry(level=LogLevel.ERROR, message="error1"),
            LogEntry(level=LogLevel.CRITICAL, message="critical1"),
        ]
        log_list.add_entries(entries)

        log_list.set_level_filter(LogLevel.WARNING)
        filtered = log_list._get_filtered_entries()
        assert len(filtered) == 3
        assert all(e.level in (LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL) for e in filtered)

    def test_text_filter(self):
        """Текстовый фильтр."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="user login"),
            LogEntry(level=LogLevel.ERROR, message="user logout"),
            LogEntry(level=LogLevel.INFO, message="connection reset"),
        ]
        log_list.add_entries(entries)

        log_list.set_text_filter("user")
        filtered = log_list._get_filtered_entries()
        assert len(filtered) == 2
        assert all("user" in e.message.lower() for e in filtered)

    def test_text_filter_specific(self):
        """Текстовый фильтр по конкретному слову."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="user login"),
            LogEntry(level=LogLevel.ERROR, message="server logout"),
            LogEntry(level=LogLevel.INFO, message="connection reset"),
        ]
        log_list.add_entries(entries)

        log_list.set_text_filter("login")
        filtered = log_list._get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].message == "user login"

    def test_combined_filters(self):
        """Комбинированный фильтр."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="user login"),
            LogEntry(level=LogLevel.ERROR, message="user logout"),
            LogEntry(level=LogLevel.ERROR, message="connection reset"),
        ]
        log_list.add_entries(entries)

        log_list.set_level_filter(LogLevel.ERROR)
        log_list.set_text_filter("user")
        filtered = log_list._get_filtered_entries()
        assert len(filtered) == 1
        assert filtered[0].level == LogLevel.ERROR
        assert "user" in filtered[0].message.lower()

    def test_empty_filter_shows_all(self):
        """Пустой фильтр показывает все."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="msg1"),
            LogEntry(level=LogLevel.ERROR, message="msg2"),
        ]
        log_list.add_entries(entries)
        log_list.set_text_filter("")
        assert len(log_list._get_filtered_entries()) == 2


class TestLogListErrorBlocks:
    """Тесты группировки ошибок."""

    def test_error_blocks_detected(self):
        """Обнаружение блоков ошибок."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="info"),
            LogEntry(level=LogLevel.ERROR, message="error1", traceback="trace1"),
            LogEntry(level=LogLevel.DEBUG, message="trace line"),
            LogEntry(level=LogLevel.INFO, message="recovered"),
            LogEntry(level=LogLevel.CRITICAL, message="critical1", traceback="trace2"),
        ]
        log_list._entries = entries
        blocks = log_list._get_error_blocks()
        assert len(blocks) >= 1

    def test_error_block_indices(self):
        """Индексы в блоках ошибок."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="info"),
            LogEntry(level=LogLevel.ERROR, message="error1"),
            LogEntry(level=LogLevel.ERROR, message="error2"),
            LogEntry(level=LogLevel.INFO, message="info2"),
        ]
        log_list._entries = entries
        blocks = log_list._get_error_blocks()
        assert len(blocks) >= 1


class TestLogListNextError:
    """Тесты перехода к ошибке."""

    def test_next_error_finds_error(self):
        """Переход к следующей ошибке."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="info"),
            LogEntry(level=LogLevel.ERROR, message="error1"),
            LogEntry(level=LogLevel.WARNING, message="warn"),
            LogEntry(level=LogLevel.CRITICAL, message="critical1"),
        ]
        log_list._entries = entries
        log_list.selected_index = 0

        with patch.object(log_list, '_safe_notify'):
            log_list.action_next_error()
            assert log_list.selected_index >= 0

    def test_next_error_no_errors(self):
        """Переход к ошибке когда её нет."""
        log_list = LogList()
        entries = [
            LogEntry(level=LogLevel.INFO, message="info"),
            LogEntry(level=LogLevel.DEBUG, message="debug"),
        ]
        log_list._entries = entries
        log_list.selected_index = 0

        with patch.object(log_list, '_safe_notify') as mock_notify:
            log_list.action_next_error()
            mock_notify.assert_called_once_with("No errors found")


class TestLogListTags:
    """Тесты тегов."""

    def test_add_tag_to_entry(self):
        """Добавление тега."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="error")
        log_list._entries = [entry]
        log_list.selected_index = 0

        with patch.object(log_list, '_safe_notify'):
            log_list.add_tag("исследовать")

        assert "исследовать" in entry.tags

    def test_add_duplicate_tag(self):
        """Дубликат тега не добавляется."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="error", tags=["tag1"])
        log_list._entries = [entry]
        log_list.selected_index = 0

        with patch.object(log_list, '_safe_notify'):
            log_list.add_tag("tag1")

        assert entry.tags.count("tag1") == 1


class TestLogListSelect:
    """Тесты выбора."""

    def test_select_entry(self):
        """Выбор записи."""
        log_list = LogList()
        entry = LogEntry(level=LogLevel.ERROR, message="test error")
        log_list._entries = [entry]
        log_list.selected_index = 0

        with patch.object(log_list, '_safe_notify'):
            log_list.action_select_entry()

        assert entry.selected is True

    def test_deselect(self):
        """Снятие выбора."""
        log_list = LogList()
        log_list.add_entries([LogEntry(level=LogLevel.INFO, message="test")])
        log_list.selected_index = 0

        log_list.action_deselect()
        assert log_list.selected_index == -1


class TestLogListFilterMode:
    """Тесты режима фильтрации."""

    def test_toggle_filter_mode_on(self):
        """Включение режима фильтрации."""
        log_list = LogList()
        log_list.action_toggle_filter_mode()
        assert log_list._filter_mode is True

    def test_toggle_filter_mode_off(self):
        """Выключение режима фильтрации очищает текст."""
        log_list = LogList()
        log_list.action_toggle_filter_mode()
        log_list._filter_text = "test"
        log_list.action_toggle_filter_mode()
        assert log_list._filter_mode is False
        assert log_list._filter_text == ""


class TestLogListDisplay:
    """Тесты отображения."""

    def test_render_no_entries(self):
        """Пустой список логов."""
        log_list = LogList()
        content = chr(10).join(log_list._build_lines())
        assert "No logs loaded" in content

    def test_render_with_entries(self):
        """Список с записями."""
        log_list = LogList()
        log_list.add_entries([
            LogEntry(level=LogLevel.ERROR, message="error msg", timestamp="2024-01-01")
        ])
        assert "No logs loaded" not in chr(10).join(log_list._build_lines())
        assert "error msg" in chr(10).join(log_list._build_lines())

    def test_render_shows_level(self):
        """Отображение уровня."""
        log_list = LogList()
        log_list.add_entries([
            LogEntry(level=LogLevel.WARNING, message="warn msg")
        ])
        assert "WARNING" in chr(10).join(log_list._build_lines())

    def test_render_shows_timestamp(self):
        """Отображение timestamp."""
        log_list = LogList()
        log_list.add_entries([
            LogEntry(level=LogLevel.INFO, message="msg", timestamp="2024-01-01 12:00:00")
        ])
        assert "2024-01-01" in chr(10).join(log_list._build_lines())
