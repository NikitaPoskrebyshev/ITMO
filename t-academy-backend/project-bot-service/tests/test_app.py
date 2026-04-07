from bot.app import BotApplication


def test_app_stores_configuration() -> None:
    app = BotApplication(token="abc", polling_timeout_seconds=30)

    assert app._token == "abc"
    assert app._polling_timeout_seconds == 30


def test_build_registers_expected_handlers() -> None:
    app = BotApplication(token="abc", polling_timeout_seconds=30)
    application = app.build()

    handler_callbacks = {type(h).__name__ for h in application.handlers.get(0, [])}

    assert "CommandHandler" in handler_callbacks
    assert "MessageHandler" in handler_callbacks
