"""Модальное окно ввода текста фильтра."""

from textual.screen import ModalScreen
from textual.widgets import Input, Label
from textual.binding import Binding


class FilterModal(ModalScreen[str | None]):
    """Модальное окно для ввода текстового фильтра.

    Пользователь вводит текст, нажимает Enter для применения или Esc для отмены.
    """

    CSS = """
    FilterModal {
        align: center middle;
        background: $background 70%;
    }

    #filter-input-container {
        width: 60;
        height: 8;
        layout: vertical;
        padding: 2;
        border: solid $primary;
        background: $surface;
    }

    #filter-label {
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
        height: 3;
        margin-top: 1;
    }

    #filter-input Input--cursor-line {
        background: $primary 30%;
    }

    #filter-actions {
        height: 3;
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
        yield Label("[bold]Фильтрация логов[/]")
        yield Label("[dim]Введите текст для поиска (Enter — применить, Esc — отмена)[/dim]")
        yield Input(
            placeholder="Поиск по сообщению, уровню или метке...",
            value=self._initial_text,
            id="filter-input",
        )
        yield Label("[dim]Enter: Применить | Esc: Отмена[/dim]")

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
