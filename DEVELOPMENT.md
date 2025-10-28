# Development Guide

Руководство по разработке для skopeo-wrapper.

## Структура проекта

```
skopeo-wrapper/
├── skopeo_wrapper/          # Основной пакет
│   ├── __init__.py         # Инициализация пакета
│   ├── skopeo_wrapper.py   # Основная логика
│   └── cli.py              # CLI интерфейс
├── tests/                   # Тесты
│   ├── __init__.py
│   └── test_skopeo_wrapper.py
├── examples/                # Примеры использования
│   ├── basic_usage.py
│   └── advanced_usage.py
├── docs/                    # Документация
├── .github/workflows/       # GitHub Actions
├── pyproject.toml          # Конфигурация проекта
├── requirements.txt        # Зависимости
├── README.md              # Основная документация
└── LICENSE                # Лицензия MIT
```

## Установка для разработки

```bash
# Клонирование репозитория
git clone https://github.com/your-username/skopeo-wrapper.git
cd skopeo-wrapper

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка в режиме разработки
pip install -e ".[dev]"
```

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ -v --cov=skopeo_wrapper --cov-report=html

# Конкретный тест
pytest tests/test_skopeo_wrapper.py::test_inspect_image -v
```

## Форматирование кода

```bash
# Форматирование с black
black skopeo_wrapper/ tests/ examples/

# Проверка стиля с flake8
flake8 skopeo_wrapper/ tests/ examples/

# Типизация с mypy
mypy skopeo_wrapper/
```

## Сборка пакета

```bash
# Установка build
pip install build

# Сборка
python -m build

# Проверка пакета
twine check dist/*
```

## Публикация в PyPI

### Тестовая публикация (TestPyPI)

```bash
# Установка twine
pip install twine

# Загрузка в TestPyPI
twine upload --repository testpypi dist/*

# Установка из TestPyPI
pip install --index-url https://test.pypi.org/simple/ skopeo-wrapper
```

### Публикация в PyPI

```bash
# Загрузка в PyPI
twine upload dist/*
```

## Версионирование

Используем семантическое версионирование (SemVer):
- `MAJOR.MINOR.PATCH`
- `1.0.0` - первый стабильный релиз
- `1.1.0` - новая функциональность
- `1.1.1` - исправления багов

## Создание релиза

1. Обновить версию в `pyproject.toml`
2. Обновить `CHANGELOG.md`
3. Создать тег: `git tag v1.0.0`
4. Запушить тег: `git push origin v1.0.0`
5. Создать релиз на GitHub

## Добавление новых функций

1. Создать ветку: `git checkout -b feature/new-feature`
2. Реализовать функцию
3. Добавить тесты
4. Обновить документацию
5. Создать Pull Request

## Отладка

```bash
# Запуск с отладкой
python -c "
from skopeo_wrapper import SkopeoWrapper
import logging
logging.basicConfig(level=logging.DEBUG)
skopeo = SkopeoWrapper()
"

# CLI с отладкой
SKOPEO_WRAPPER_DEBUG=1 skopeo-wrapper copy docker://alpine:latest dir:/tmp/test
```

## Требования к коду

- Python 3.7+ совместимость
- Типизация с type hints
- Документация для всех публичных функций
- Покрытие тестами > 80%
- Соответствие PEP 8

## Полезные команды

```bash
# Очистка
rm -rf build/ dist/ *.egg-info/
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Проверка безопасности
pip install safety
safety check

# Проверка зависимостей
pip install pipdeptree
pipdeptree
```
