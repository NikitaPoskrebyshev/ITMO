# CLAUDE.md

## Development commands

```bash
# Install dependencies
poetry install --no-root --with dev

# Run all tests
PYTHONPATH=src poetry run pytest tests

# Run a single test
PYTHONPATH=src poetry run pytest tests/test_link_api.py::test_add_github_link

# Lint (black format + mypy + ruff + dead fixture check)
make lint
```

Run the service: `cd src && python main.py` (copy `config.example.toml` → `config.toml` first).

---

## Project overview

This repository contains the **scrapper-service** for homework 2.

The scrapper-service is responsible for:

- storing tracked links for Telegram users (via chatId)
- managing subscriptions (add/remove/list links)
- polling external APIs (GitHub, StackOverflow) to detect updates
- running a background scheduler
- sending update notifications to bot-service via HTTP

This service is the **source of truth** for all tracked links.

---

## IMPORTANT: strict service boundaries

This repository must contain ONLY scrapper logic.

### Do NOT implement here:

- Telegram bot logic
- Telegram handlers
- user dialogs or state machines
- direct interaction with Telegram API
- bot command handling (`/track`, `/list`, etc.)

Those belong to **bot-service**.

### This service communicates with bot-service ONLY via HTTP

- outgoing: `POST /updates` → bot-service
- no Telegram logic here

---

## Main homework goal

Implement a backend service that:

1. stores tracked links per chat
2. exposes HTTP API (according to OpenAPI contract)
3. periodically checks links for updates
4. notifies bot-service when updates are detected

---

## Required HTTP API

The service must expose endpoints matching the OpenAPI contract.

Minimum required endpoints:

### Chat management

- `POST /tg-chat/{id}`
  - register Telegram chat

- `DELETE /tg-chat/{id}`
  - delete chat
  - return error if chat does not exist

---

### Link management

- `GET /links`
  - return list of tracked links for a chat

- `POST /links`
  - add new link for a chat
  - must validate:
    - chat exists
    - link is valid
    - link is not already tracked for this chat

- `DELETE /links`
  - remove link from a chat
  - must validate:
    - chat exists
    - link exists for that chat

---

## Data storage

Use **in-memory storage only** (no database in this homework).

Recommended approach:

- repository pattern

Suggested structures:

- chats: `set[int]`
- links:
  - list or dict of objects:
    - url
    - chat_id(s)
    - tags
    - last_checked_at
    - last_known_update

Design should allow:

- multiple chats tracking same link
- efficient lookup per chat

Do not overengineer.

---

## Domain models

You will likely need:

- `TrackedLink`
- `Chat`
- `AddLinkRequest`
- `RemoveLinkRequest`
- `LinkResponse`
- `LinkUpdate` (for bot-service)

Models must match OpenAPI contract.

---

## Link validation and parsing

Supported link types:

- GitHub repositories
  - example: https://github.com/user/repo

- StackOverflow questions
  - example: https://stackoverflow.com/questions/{id}/...

You must:

- detect link type
- extract identifiers:
  - GitHub → owner + repo
  - StackOverflow → question_id

Reject invalid links.

---

## External HTTP clients

You must implement clients manually (no SDKs allowed):

### GitHub client

- call GitHub REST API
- retrieve last update info:
  - `updated_at` or similar

### StackOverflow client

- call StackExchange API
- retrieve:
  - `last_activity_date`

### Requirements

- no official SDKs (PyGithub, etc.)
- use plain HTTP client
- handle:
  - non-2xx responses
  - malformed responses
- never crash on external API failure

---

## Scheduler

Implement a background scheduler.

Responsibilities:

1. iterate over tracked links
2. fetch current state from external APIs
3. compare with stored state
4. if updated:
   - send notification to bot-service
5. update stored state

Simplified logic is enough:
- only detect that something changed (timestamp difference)

No need for detailed diff yet.

---

## Communication with bot-service

Scrapper must send HTTP requests:

- `POST /updates` to bot-service

Payload:

- must match `LinkUpdate` contract

Include:

- link
- chat ids (or one chat depending on implementation)
- update info (can be minimal)

Use a dedicated HTTP client:

- `BotClient` or similar

---

## Error handling

The service must never crash due to:

- invalid user input
- bad HTTP requests
- external API failures

Handle:

- invalid links
- unknown chats
- duplicate links
- removing non-existing links
- bad external API responses

Return proper HTTP status codes:

- 200 → success
- 400 → bad request
- 404 → not found

---

## Testing requirements

Tests are mandatory.

### Must cover:

#### Chat API
- register chat
- delete chat
- delete non-existing chat

#### Link API
- add link
- remove link
- list links
- add link to non-existing chat (error)
- remove link from non-existing chat (error)

#### External clients
- success response
- non-2xx response
- invalid JSON

#### Scheduler
- detects update
- sends notification
- does not crash on failures

### Important

- DO NOT call real APIs in tests
- use mocks/stubs

---

## Code structure (recommended)

- `handlers/` → HTTP endpoints
- `services/` → business logic
- `repositories/` → in-memory storage
- `clients/`
  - `github_client.py`
  - `stackoverflow_client.py`
  - `bot_client.py`
- `scheduler/`
- `models/`
- `config/`

Use existing project structure if present.

---

## Configuration

Use typed configuration.

Possible fields:

- server host/port
- bot-service base URL
- scheduler interval
- HTTP timeouts

Do not hardcode values.

---

## Logging

Use structured logging.

Include:

- event name
- chat_id
- url
- error type

Examples:

- `chat_registered`
- `link_added`
- `link_removed`
- `update_detected`
- `external_api_failed`

---

## Implementation priorities

Follow this order:

1. HTTP server + basic routing
2. chat endpoints
3. link endpoints
4. in-memory repository
5. tests for API
6. link parsing
7. external clients
8. scheduler
9. bot HTTP client
10. integration logic

---

## Constraints for Claude Code

When modifying this repository:

- do not introduce Telegram logic
- do not implement bot commands
- do not use external SDKs
- do not add unnecessary dependencies
- do not rewrite architecture completely
- prefer small, incremental changes
- keep code testable

---

## Definition of done

The scrapper-service is complete when:

- all required endpoints work correctly
- links are stored and managed per chat
- invalid operations return proper errors
- GitHub and StackOverflow updates are detected
- scheduler runs and triggers updates
- bot-service receives `POST /updates`
- tests cover positive and negative scenarios
- no Telegram logic exists in this repository
