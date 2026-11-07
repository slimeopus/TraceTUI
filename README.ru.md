# TraceTUI

<p align="left">
  <a href="./README.md">🇺🇸 English</a> • 
  <a href="./README.ru.md">🇷🇺 Русский</a>
</p>

**Интерактивный TUI-дебаггер для логов** — красивый консольный интерфейс на базе [Textual](https://textual.io/), который парсит логи (`loguru`, `logging`) в реальном времени, подсвечивает ошибки и позволяет фильтровать их стрелками.

![Tests](https://github.com/slimeopus/TraceTUI/actions/workflows/tests.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/github/license/slimeopus/TraceTUI)
![Version](https://img.shields.io/badge/version-2.0.0-34C4C4.svg?style=flat)

![Preview](.github/assets/preview.png)

## ✨ Возможности

### Трёхпанельный интерфейс
- **Левая панель** — список источников/файлов логов с индикаторами активности
- **Центральная панель** — поток логов с цветовой кодировкой уровней
- **Правая панель** — детали выбранной строки (traceback, метаданные, теги)

### Форматы логов
- **loguru** — `2024-01-15 10:30:45 \| ERROR \| module.py:42 - message`
- **logging** — `2024-01-15 10:30:45,123 - module.name - ERROR - message`
- **Simple** — `ERROR - message`
- **Auto-detect** — автоматическое определение формата

### Навигация и управление

#### Движение по логам
- `↑` / `↓` — навигация по логам (по строкам)
- Блоки ошибок подсвечиваются при наведении

#### Переключение источников
- `←` / `→` — переключение между источниками/файлами логов
- Активный источник отмечен маркером `▸` в левой панели

#### Горячие клавиши
| Клавиша | Действие | Описание |
|---------|----------|----------|
| `F` | Filter | Режим фильтрации — введите текст для поиска |
| `E` | Next Error | Переход к следующей ошибке (пропуск INFO/DEBUG) |
| `T` | Theme | Переключение темы (светлая/тёмная) |
| `Q` | Quit | Выход из приложения |

#### Дополнительные возможности
- Копирование traceback в буфер обмена
- Добавление пользовательских меток (тегов)
- Фильтрация по уровню и тексту
- Поддержка нескольких файлов логов одновременно
- **Timeline Merge Mode** (`m`) — сквозной таймлайн из нескольких файлов с цветовой маркировкой источников

## 📦 Установка

### Через pip
```bash
pip install tracetui
```

### Из исходников
```bash
git clone <repository-url>
cd TraceTUI
pip install -e .
```

### Зависимости
- Python >= 3.10
- textual >= 1.0.0
- rich >= 13.0.0

## 🚀 Использование

### Быстрый старт
```bash
# Запуск с примерами
tracetui sample_logs/app_standard.log
tracetui sample_logs/app_loguru.log

# Несколько файлов
tracetui log1.log log2.log log3.log

# С указанием формата
tracetui -f loguru my_app.log
tracetui -f logging server.log

# Несколько файлов (режим timeline — нажмите m в UI)
tracetui app.log worker.log scheduler.log

# Фильтрация по уровню
tracetui -l ERROR app.log
```

### Программное использование
```python
from tracetui.app import TraceTUIApp
from tracetui.parsers.log_parser import load_log_source
from pathlib import Path

app = TraceTUIApp()

# Загрузка файла
source = load_log_source(Path("app.log"))
app.add_log_source(source)

# Запуск
app.run()
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# С отчетом
pytest -v

# С покрытием
pytest --cov=tracetui --cov-report=html
```

## 📝 Примеры использования

### Отладка приложения с множеством ошибок
```bash
# Открываем лог с автоопределением формата
tracetui /var/log/myapp.log

# Перемещаемся стрелками до ERROR
# Нажимаем Enter для просмотра деталей
# Смотрим traceback в правой панели
# Нажимаем 'd' чтобы пометить как "исследовать"
```

### Мониторинг нескольких файлов
```bash
# Открываем несколько логов одновременно
tracetui app.log worker.log scheduler.log
```

## 📄 Лицензия

MIT

---
