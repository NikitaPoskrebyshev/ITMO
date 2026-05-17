# LinkTracker Bot

## Требования

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/products/docker-desktop/)
- Запущенные PostgreSQL, Kafka и scrapper-service (см. README в `project-scrapper-service`)

## Запуск

```bash
poetry install

cp config.example.toml config.toml
# Вставить Telegram-токен в config.toml

poetry run python src/main.py
```

## Механизм получения нотификаций

Задаётся в `config.toml` через параметр `transport`:

```toml
[notification]
transport = "kafka"  # "kafka" или "http"
```
## Тесты

```bash
# Без Docker
poetry run pytest tests/ --ignore=tests/test_repositories.py --ignore=tests/test_integration_kafka.py

# С Docker (тесты БД через testcontainers)
poetry run pytest tests/test_repositories.py -v

# Интеграционный тест Scraper → Kafka → Bot (testcontainers Kafka)
poetry run pytest tests/test_integration_kafka.py -v

# Все тесты
poetry run pytest
```
