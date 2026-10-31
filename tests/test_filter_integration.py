"""Тесты интеграции модального окна фильтрации с LogList."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tracetui.widgets.log_list import LogList
from tracetui.widgets.filter_input import FilterModal
from tracetui.models import LogEntry, LogLevel


class TestFilterIntegration:
    """Тесты интеграции фильтрации."""

    def test_action_toggle_filter_mode_calls_push_screen(self):
        """Проверка что action_toggle_filter_mode вызывает push_screen."""
        log_list = LogList()

        # Создаём мок-приложение
        mock_app = MagicMock()
        # Присваиваем мок напрямую как атрибут класса
        LogList.app = property(lambda self: mock_app)

        # Вызываем action
        log_list.action_toggle_filter_mode()

        # Проверяем что push_screen был вызван с FilterModal
        mock_app.push_screen.assert_called_once()
        args, kwargs = mock_app.push_screen.call_args
        modal = args[0]
        assert isinstance(modal, FilterModal)

    def test_action_toggle_filter_mode_clears_filter(self):
        """Проверка что фильтр очищается перед открытием модального окна."""
        log_list = LogList()
        log_list._filter_text = "existing_filter"

        # Создаём мок-приложение
        mock_app = MagicMock()
        LogList.app = property(lambda self: mock_app)

        # Вызываем action
        log_list.action_toggle_filter_mode()

        # Проверяем что фильтр очищен
        assert log_list._filter_text == ""

    def test_action_toggle_filter_mode_with_active_filter(self):
        """Проверка сброса существующего фильтра."""
        log_list = LogList()
        log_list._filter_text = "test_filter"

        # Создаём мок-приложение
        mock_app = MagicMock()
        LogList.app = property(lambda self: mock_app)

        # Вызываем action (должен сбросить фильтр и открыть модальное окно)
        log_list.action_toggle_filter_mode()

        # Фильтр должен быть очищен
        assert log_list._filter_text == ""

    def test_handle_filter_result_with_text(self):
        """Проверка применения текста фильтра."""
        log_list = LogList()

        # Добавляем тестовые записи
        entry1 = LogEntry(level=LogLevel.INFO, message="Test message 1")
        entry2 = LogEntry(level=LogLevel.ERROR, message="Error message")
        log_list._entries = [entry1, entry2]

        # Применяем фильтр
        log_list._handle_filter_result("Error")

        assert log_list._filter_text == "Error"
        assert log_list._selectedIndex == -1

    def test_handle_filter_result_empty(self):
        """Проверка очистки фильтра пустым текстом."""
        log_list = LogList()
        log_list._entries = [
            LogEntry(level=LogLevel.INFO, message="Test 1"),
        ]
        log_list._filter_text = "test"

        # Очищаем фильтр
        log_list._handle_filter_result("")

        assert log_list._filter_text == ""

    def test_handle_filter_result_cancel(self):
        """Проверка отмены фильтрации по Esc."""
        log_list = LogList()
        log_list._filter_text = "test"

        # Отменяем (None)
        log_list._handle_filter_result(None)

        # Фильтр не должен меняться при отмене
        assert log_list._filter_text == "test"

    def test_no_app_graceful_handling(self):
        """Проверка что без app не падает, а показывает уведомление."""
        log_list = LogList()

        # self.app выбрасывает NoActiveAppError, когда нет активного приложения
        # Действие должно завершиться gracefully
        # Не должно вызывать необработанных исключений
        try:
            log_list.action_toggle_filter_mode()
        except Exception as e:
            pytest.fail(f"Должно обрабатывать отсутствие app gracefully, но получено: {e}")
