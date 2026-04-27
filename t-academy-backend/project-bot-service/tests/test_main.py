from pathlib import Path

from bot.config import AppConfig, TelegramConfig
from main import main


def test_main_builds_application_and_runs(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[telegram]\ntoken = "test-token"\npolling_timeout_seconds = 15\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "main.load_config",
        lambda: AppConfig(
            telegram=TelegramConfig(token="test-token", polling_timeout_seconds=15)
        ),
    )

    captured: dict[str, object] = {}

    class FakeBotApplication:
        def __init__(
            self, token: str, polling_timeout_seconds: int, **kwargs: object
        ) -> None:
            captured["token"] = token
            captured["polling_timeout_seconds"] = polling_timeout_seconds

        def run(self) -> None:
            captured["run_called"] = True

    monkeypatch.setattr("main.BotApplication", FakeBotApplication)

    main()

    assert captured == {
        "token": "test-token",
        "polling_timeout_seconds": 15,
        "run_called": True,
    }
