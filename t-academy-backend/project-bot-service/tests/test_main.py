from pathlib import Path

from bot.config import AppConfig, ScrapperConfig, ServerConfig, TelegramConfig
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
            telegram=TelegramConfig(token="test-token", polling_timeout_seconds=15),
            scrapper=ScrapperConfig(base_url="http://scrapper:8080", timeout_seconds=5),
            server=ServerConfig(host="0.0.0.0", port=8081),
        ),
    )

    captured: dict[str, object] = {}

    class FakeBotApplication:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["run_called"] = True

    monkeypatch.setattr("main.BotApplication", FakeBotApplication)

    main()

    assert captured["token"] == "test-token"
    assert captured["polling_timeout_seconds"] == 15
    assert captured["scrapper_base_url"] == "http://scrapper:8080"
    assert captured["run_called"] is True
