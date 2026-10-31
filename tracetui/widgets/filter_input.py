"""Модальное окно ввода текста фильтра."""

from textual.screen import ModalScreen
from textual.widgets import Input, Label
from textual.containers import Vertical
from textual.binding import Binding


class FilterModal(ModalScreen[str | None]):
    """Модальное окно для ввода текстового фильтра.

    Пользователь вводит текст, нажимает Enter для применения или Esc для отмены.
    """

    CSS = """
    FilterModal {
        align: center middle;
        background: $surface 70%;
    }

    #filter-container {
        width: 60;
        height: auto;
        padding: 2;
        border: solid $primary;
        background: $boost;
        layout: vertical;
        align: center middle;
    }

    #filter-title {
        text-align: center;
        height: 1;
        text-style: bold;
        color: $primary;
    }

    #filter-hint {
        text-align: center;
        height: 1;
        text-style: dim;
        color: $text-muted;
    }

    #filter-input {
        width: 50;
        height: 3;
        margin-top: 1;
    }

    #filter-actions {
        height: 2;
        margin-top: 1;
        text-align: center;
        text-style: dim;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, initial_text: str = "", **kwargs):
        """Инициализация модального окна.

        Args:
            initial_text: Начальный текст в поле ввода (если применяем существующий фильтр).
        """
        super().__init__(**kwargs)
        self._initial_text = initial_text

    def compose(self):
        """Создание интерфейса модального окна."""
        with Vertical(id="filter-container"):
            yield Label("[bold]Фильтрация логов[/]", id="filter-title")
            yield Label("[dim]Введите текст для поиска[/dim]", id="filter-hint")
            yield Input(
                placeholder="Поиск по сообщению, уровню или метке...",
                value=self._initial_text,
                id="filter-input",
            )
            yield Label("[dim]Enter: Применить | Esc: Отмена[/dim]", id="filter-actions")

    def action_cancel(self) -> None:
        """Отмена фильтрации."""
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обработка нажатия Enter."""
        value = event.value.strip()
        if value:
            self.dismiss(value)
        else:
            # Если поле пустое — снимаем фильтр
            self.dismiss("")
