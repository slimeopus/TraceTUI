"""Конфигурация pytest."""

import sys
from pathlib import Path

# Добавляем корень проекта в путь для импорта
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
