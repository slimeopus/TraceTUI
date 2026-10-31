"""Тесты для модального окна фильтрации."""

from tracetui.widgets.filter_input import FilterModal


class TestFilterModal:
    """Тесты модального окна фильтрации."""

    def test_initial_value(self):
        """Проверка начального значения."""
        modal = FilterModal(initial_text="test")
        assert modal._initial_text == "test"

    def test_empty_initial_value(self):
        """Проверка пустого начального значения."""
        modal = FilterModal()
        assert modal._initial_text == ""
