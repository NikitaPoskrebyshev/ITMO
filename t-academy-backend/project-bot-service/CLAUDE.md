   # CLAUDE.md

## Project overview

This repository contains the **bot-service** part of the homework.
The bot-service is responsible only for:

- interacting with Telegram users
- handling bot commands
- managing the `/track` dialog as a state machine
- calling the external **scrapper-service** over HTTP
- accepting update notifications from scrapper over HTTP
- sending Telegram notifications to users

The bot-service must **not** implement background link checking logic, polling external APIs like GitHub/StackOverflow directly, or storing scraping logic. That belongs to the separate `scrapper-service`.

---

## Main homework goal for this repository

Implement the bot-side functionality for homework 2.

### Required user commands

The bot must support:

- `/start`
- `/help`
- `/track`
- `/untrack`
- `/list`
- `/cancel`

### Required behavior

#### `/track`
`/track` must work as a **dialog**, not as a one-line command.

Expected flow:

1. user sends `/track`
2. bot asks for a link
3. user sends a link
4. bot validates the link format
5. bot asks for tags
6. user sends tags separated by commas, or sends an empty message / skip-like input if supported by current architecture
7. bot calls scrapper-service over HTTP to save the subscription
8. bot sends a success or error message

Rules:

- if the user sends `/cancel`, the process is cancelled
- if the user sends another command during the dialog, current tracking flow is cancelled
- if the link is invalid, bot must explain that the link is invalid
- if the link is already tracked, bot must respond with: `Ссылка уже отслеживается`

#### `/untrack`
Expected flow:

1. user sends `/untrack`
2. bot asks for the link or accepts it depending on current implementation style
3. bot calls scrapper-service to remove the tracked link
4. bot sends success or error message

#### `/list`
Expected behavior:

- show all tracked links for the current user
- optionally support tag filtering if command format in current implementation allows it
- if list is empty, bot sends a special message saying there are no tracked links

#### Unknown commands
Unknown commands should not crash the bot.
Bot should ignore them with a user-friendly message.

---

## Service boundaries

### bot-service responsibilities

This repository should contain:

- Telegram handlers
- command routing
- state machine for `/track`
- request/response DTOs for communication with scrapper
- HTTP client for calling scrapper-service
- HTTP endpoint `/updates` for receiving notifications from scrapper
- formatting outgoing Telegram messages
- in-memory bot-side conversational state if needed

### forbidden in bot-service

Do **not** implement here:

- background scheduler for checking links
- GitHub API polling
- StackOverflow API polling
- scraping logic
- repository of tracked links as the source of truth for the whole system
- business logic that belongs to scrapper-service

The source of truth for tracked links must be the scrapper-service.

---

## Architecture guidance

Preserve and extend the current project structure.
Prefer minimal changes to existing code.
Do not rewrite working code without a strong reason.

Recommended layers:

- **handlers**: Telegram command handlers and HTTP handlers
- **services/use-cases**: orchestration logic
- **clients**: HTTP clients for scrapper-service
- **repositories/state**: only bot-local conversational state if needed
- **models/dto**: request/response payloads and domain objects
- **config**: typed configuration models
- **logging**: structured logging helpers

Keep business logic out of Telegram handlers when possible.

---

## State machine requirements

The `/track` command must be implemented as an explicit state machine.

Suggested states:

- `IDLE`
- `WAITING_FOR_TRACK_URL`
- `WAITING_FOR_TRACK_TAGS`

Per-chat state is enough for this homework.

Suggested transitions:

- `/track` from `IDLE` -> `WAITING_FOR_TRACK_URL`
- valid URL received -> `WAITING_FOR_TRACK_TAGS`
- tags received -> back to `IDLE`
- `/cancel` from any non-idle state -> `IDLE`
- any other command during non-idle state -> cancel current flow and process command normally or notify cancellation, depending on current architecture

Store only minimal conversational state:

- current state
- pending URL
- maybe pending chat/user id

Do not overengineer this.

---

## HTTP integration with scrapper-service

The bot-service must call scrapper-service over HTTP.

Expected operations on the client side:

- register Telegram chat
- add tracked link
- remove tracked link
- list tracked links

Implement a dedicated client abstraction, for example:

- `ScrapperClient`
- `ScrapperHttpClient`

The rest of the bot code should depend on an interface/protocol, not directly on low-level HTTP calls.

### Important
Claude should not invent endpoint formats.
When implementing HTTP requests, read the homework contract / existing spec and match it exactly.

If request/response schemas already exist in the project, reuse them.
If they do not exist, create clear DTOs matching the contract.

---

## Incoming HTTP endpoint in bot-service

The bot-service must expose an HTTP endpoint:

- `POST /updates`

This endpoint is used by scrapper-service to notify the bot about detected updates.

Requirements:

- parse incoming JSON
- validate required fields
- reject malformed payloads with non-200 response
- for valid payloads, send a Telegram notification to the appropriate user(s)
- notification text can be simple for this homework; full update details are not required yet

Keep the endpoint thin:
validation + delegate to service.

---

## Error handling rules

Follow these principles:

- never crash on invalid user input
- never crash on malformed incoming HTTP payload
- external HTTP failures must be handled gracefully
- provide user-friendly Telegram messages
- log technical details with structured logging

Examples of cases that must be handled:

- invalid link format
- duplicate tracked link
- scrapper unavailable
- scrapper returned error response
- bad `/updates` payload
- missing Telegram message/user/chat in update object

Do not swallow exceptions silently.

---

## Testing requirements

Tests are required.
Prefer AAA style: Arrange, Act, Assert.

### Must cover

#### Telegram command tests
- `/track` happy path
- `/track` with invalid link
- `/track` duplicate link
- `/cancel`
- another command during `/track` flow
- `/list` when empty
- `/list` when non-empty
- `/untrack`

#### HTTP endpoint tests
- valid `POST /updates` returns 200
- invalid `POST /updates` returns non-200

#### Service/client tests
- scrapper client success path
- scrapper client error handling
- timeout / network failure behavior if the current stack supports easy testing of it

### Important
Tests must not perform real external network calls.
Use mocks/stubs/fakes.

---

## Code style instructions

When editing code in this repository, follow these rules:

- make **minimal, targeted changes**
- preserve current naming and project style where reasonable
- prefer small functions
- avoid duplication
- keep handlers thin
- use type hints everywhere practical
- do not introduce new dependencies unless explicitly required
- do not replace existing architecture if it can be extended cleanly
- avoid magic strings; extract user-visible messages/constants where appropriate
- use structured logging with key-value fields

---

## Logging requirements

Use structured logging.

Good:
- event name
- chat id
- user id
- command name
- URL
- error type

Bad:
- huge formatted strings with all data embedded into message text only

Examples of useful events:

- `track_started`
- `track_cancelled`
- `track_link_received`
- `track_completed`
- `track_duplicate_link`
- `scrapper_request_failed`
- `updates_received`
- `updates_validation_failed`

---

## Configuration requirements

Use typed configuration.

Possible config fields:

- Telegram bot token
- scrapper base URL
- bot host
- bot port
- request timeout values

Do not hardcode secrets.
Do not commit tokens.
Use the project’s existing config approach and extend it consistently.

---

## Implementation priorities

When working on this repository, implement in this order:

1. scrapper HTTP client abstraction
2. `/track` state machine
3. `/untrack`
4. `/list`
5. `/updates` HTTP endpoint
6. tests
7. logging cleanup / refinement

---

## Constraints for Claude Code

When making changes in this repository:

- do not touch unrelated files
- do not rewrite the whole project
- do not move logic into scrapper-service from here
- do not add unsupported dependencies
- do not remove existing working handlers unless replacing them with clearly better equivalents
- always keep bot-service focused on Telegram + HTTP integration responsibilities only

If the repository already contains repository-pattern abstractions, handler classes, config models, or logging helpers, extend them instead of introducing a parallel architecture.

---

## If generating code

When generating code for this repository:

- prefer production-like code over pseudo-code
- include type hints
- keep imports clean
- keep functions testable
- avoid unnecessary comments
- ensure new code is compatible with the current project conventions
- preserve async style if the existing bot uses async handlers

---

## Likely entities to add

Depending on current repository structure, likely additions include:

- track dialog state enum
- per-chat tracking session model
- in-memory conversation state repository
- scrapper client interface + implementation
- DTOs for add/remove/list links
- DTO for incoming link update
- HTTP route/controller for `/updates`
- service for formatting update messages

Use the existing project layout first; only create new modules when necessary.

---

## Definition of done for bot-service

The work in this repository is complete when:

- `/track`, `/untrack`, `/list`, `/cancel` behave correctly
- `/track` is implemented as a dialog/state machine
- bot communicates with scrapper via HTTP
- bot exposes `POST /updates`
- malformed update payloads are rejected
- valid update payloads trigger Telegram notifications
- tests cover positive and negative scenarios
- logging is structured
- config is typed
- no scraping or scheduler logic is implemented here
