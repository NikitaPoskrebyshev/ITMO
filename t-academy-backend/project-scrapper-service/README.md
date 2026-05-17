# Scrapper Service

## Требования

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/products/docker-desktop/)

## Запуск

```bash
poetry install

docker compose up -d postgres-scrapper postgres-bot kafka-0 kafka-1 kafka-2 kafka-init kafka-ui valkey-primary valkey-replica-1 valkey-replica-2
docker compose ps # проверка healthy

cp config.example.toml config.toml
# Заполнить config.toml

# Запустить сервис
poetry run python src/main.py
```

## Инфраструктура

`docker compose up -d` поднимает:

| Сервис | Порт | Описание |
|---|---|---|
| postgres-scrapper | 5432 | БД scrapper-service |
| postgres-bot | 5433 | БД bot-service |
| kafka-0 | 9094 | Kafka брокер 0 |
| kafka-1 | 9095 | Kafka брокер 1 |
| kafka-2 | 9096 | Kafka брокер 2 |
| kafka-ui | 8090 | Kafka UI (мониторинг) |
| valkey-primary | 6379 | Valkey primary (кэш) |
| valkey-replica-1 | — | Valkey replica 1 |
| valkey-replica-2 | — | Valkey replica 2 |

Kafka UI доступен по адресу: http://localhost:8090

## Кэширование

Результаты GET `/links` кэшируются в Valkey по ключу `links:{tg_chat_id}`.
Кэш инвалидируется при добавлении и удалении ссылок.

Настраивается в `config.toml`:

```toml
[valkey]
url = "redis://localhost:6379"
ttl_seconds = 60
```

Если секция `[valkey]` отсутствует — кэширование отключено.

## Механизм отправки нотификаций

Задаётся в `config.toml` через параметр `transport`:

```toml
[notification]
transport = "kafka"  # "kafka" или "http"
```

По умолчанию используется Kafka.

## Тесты

```bash
# Без Docker
poetry run pytest tests/ --ignore=tests/test_repositories.py --ignore=tests/test_cache.py

# С Docker (тесты репозиториев через testcontainers)
poetry run pytest tests/test_repositories.py -v

# Тесты кэша (testcontainers Redis)
poetry run pytest tests/test_cache.py -v

# Все тесты
poetry run pytest
```
