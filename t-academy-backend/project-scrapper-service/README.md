# Scrapper Service

## Требования

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/products/docker-desktop/)

## Запуск

```bash
poetry install

cp config.example.toml config.toml
# Заполнить config.toml

# Запустить PostgreSQL
docker compose up -d

# Запустить сервис
poetry run python src/main.py
```

## Тесты

```bash
# Без Docker
poetry run pytest tests/ --ignore=tests/test_repositories.py

# С Docker (тесты репозиториев через testcontainers)
poetry run pytest tests/test_repositories.py -v

# Все тесты
poetry run pytest
```
