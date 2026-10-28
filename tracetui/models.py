"""Модели данных для логов."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class LogLevel(Enum):
    """Уровни логирования."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @property
    def color(self) -> str:
        """Возвращает цвет для уровня лога."""
        return {
            self.DEBUG: "grey50",
            self.INFO: "white",
            self.WARNING: "orange1",
            self.ERROR: "red1",
            self.CRITICAL: "bright_red",
        }[self]

    @property
    def icon(self) -> str:
        """Возвращает иконку для уровня лога."""
        return {
            self.DEBUG: "⚬",
            self.INFO: "ℹ",
            self.WARNING: "⚠",
            self.ERROR: "✕",
            self.CRITICAL: "✕",
        }[self]


@dataclass
class LogEntry:
    """Одна запись лога."""

    level: LogLevel
    message: str
    timestamp: str = ""
    logger_name: str = ""
    file_path: str = ""
    line_number: int = 0
    traceback: str = ""
    tags: list[str] = field(default_factory=list)
    selected: bool = False

    @property
    def formatted_line(self) -> str:
        """Форматированная строка для отображения."""
        parts = []
        if self.timestamp:
            parts.append(self.timestamp)
        if self.logger_name:
            parts.append(f"[{self.logger_name}]")
        parts.append(f"{self.level.value}:")
        parts.append(self.message)
        return " ".join(parts)


@dataclass
class LogSource:
    """Источник логов (файл или поток)."""

    name: str
    path: Path
    format_type: str = "auto"  # auto, loguru, logging, custom
    entries: list[LogEntry] = field(default_factory=list)
    is_active: bool = False
    has_new: bool = False

    @property
    def entry_count(self) -> int:
        return len(self.entries)
