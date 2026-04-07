# LinkTracker Bot

## Запуск

1. Скопируйте шаблон конфигурации:
   ```bash
   cp config.example.toml config.toml
   ```
2. Вставьте токен бота в `config.toml`.
3. Установите зависимости:
   ```bash
   poetry install
   ```
4. Запустите приложение:
   ```bash
   poetry run python src/main.py
   ```

## Запуск тестов

```bash
poetry run pytest
```
