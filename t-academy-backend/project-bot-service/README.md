# LinkTracker Bot

## Требования

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- Запущенные PostgreSQL и scrapper-service (см. README в `project-scrapper-service`)

## Запуск

```bash
poetry install

cp config.example.toml config.toml
# Вставить Telegram-токен в config.toml

poetry run python src/main.py
```

## Тесты

```bash
# Без Docker
poetry run pytest tests/ --ignore=tests/test_repositories.py

# С Docker (тесты БД через testcontainers)
poetry run pytest tests/test_repositories.py -v

# Все тесты
poetry run pytest
```
