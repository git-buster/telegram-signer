# Telegram Signer

Telegram Signer is a Python CLI tool for scheduled Telegram check-ins. It can send
configured check-in messages, click inline keyboard buttons, handle topic IDs, keep
SQLite check-in records, and optionally use an OpenAI-compatible API for image or
math-style verification steps.

This fork is intentionally focused on check-ins only. It does not include extra
dashboard or message-watching features.

## Features

- Required account name in every command: `telegram-signer <account> ...`
- Scheduled check-in tasks with cron-style or time-style schedules
- Legacy config compatibility for existing signer `config.json` files
- SQLite check-in record storage with lazy migration from `sign_record.json`
- Telegram forum topic support through `message_thread_id`
- Action flow support:
  - send text
  - send dice
  - click a button by text
  - choose an option by image through an LLM
  - reply to a calculation prompt through an LLM
  - click captcha buttons according to a slot-machine dice result

## Installation

Requires Python 3.10 or newer.

```sh
pip install -U telegram-signer
```

## Command Format

The account name is required and comes before the command:

```sh
telegram-signer account_a login
telegram-signer account_a logout
telegram-signer account_a run task_name
```

Run multiple accounts with your shell by starting separate processes. Keep this to
five accounts or fewer:

```sh
telegram-signer account_a run task_a &
telegram-signer account_b run task_b &
telegram-signer account_c run task_c &
```

## Common Commands

```sh
telegram-signer account_a login
telegram-signer account_a logout
telegram-signer account_a list
telegram-signer account_a reconfig task_name
telegram-signer account_a run task_name
telegram-signer account_a run-force task_name
telegram-signer account_a list-records task_name
telegram-signer account_a migrate-records
telegram-signer account_a llm-config
```

Global options must be placed before the account name:

```sh
telegram-signer --workdir .signer account_a run task_name
```

## Config Compatibility

Existing signer configs remain supported. The default path is:

```text
<workdir>/telegram-signer/config/<task_name>/config.json
```

Older signer config versions are still migrated through the existing compatibility
chain. Existing configs from the older path are still read and copied to the new
path when loaded:

```text
<workdir>/signs/<task_name>/config.json
```

Check-in records use SQLite at:

```text
<workdir>/data.sqlite3
```

Legacy record files are still readable and can be migrated:

```text
<workdir>/signs/<task_name>/<user_id>/sign_record.json
<workdir>/signs/<task_name>/sign_record.json
```

## Example Config

```json
{
  "chats": [
    {
      "chat_id": "@target_bot_or_group",
      "message_thread_id": null,
      "name": "daily check-in",
      "delete_after": null,
      "actions": [
        {"action": 1, "text": "/checkin"},
        {"action": 3, "text": "Check in"},
        {"action": 6, "if_dice_emoji": "🎰"}
      ],
      "action_interval": 1
    }
  ],
  "sign_at": "0 6 * * *",
  "random_seconds": 0,
  "sign_interval": 1
}
```

Action IDs:

| ID | Action |
| --- | --- |
| 1 | send text |
| 2 | send dice |
| 3 | click keyboard button by text |
| 4 | choose option by image |
| 5 | reply to calculation prompt |
| 6 | solve slot-machine captcha buttons when an `if_*` condition matches |

Slot-machine captcha solving is intentionally conditional. Add at least one of
these fields to an `action: 6` step:

```json
{"action": 6, "if_dice_emoji": "🎰"}
{"action": 6, "if_text": "choose the symbols"}
{"action": 6, "if_regex": "slot|captcha|verification"}
```

If no `if_*` condition is present, the action is skipped.

### Slot-machine Captcha Notes

Some Telegram bots send a slot-machine dice result first, then send a prompt
asking which symbols were shown. The decoded symbols are named `bar`, `grapes`,
`lemon`, and `seven`.

Observed button mapping:

| Button | Meaning |
| --- | --- |
| `➖` | BAR |
| `🍇` | grapes |
| `🍋` | lemon |
| `7️⃣` | seven |
| `🔙` | back |

`➖` is Unicode `U+2796` and is commonly called heavy minus sign. In this
captcha it represents BAR. `🔙` is the back/cancel button and must not be used
as BAR fallback.

Example diagnostic log:

```text
Slot-machine captcha value=33, symbols=('bar', 'bar', 'lemon'), buttons=[
  "text='➖', normalized='➖', callback='captcha_➖_signin_...'",
  "text='🍇', normalized='🍇', callback='captcha_🍇_signin_...'",
  "text='🍋', normalized='🍋', callback='captcha_🍋_signin_...'",
  "text='7️⃣', normalized='7⃣', callback='captcha_7️⃣_signin_...'",
  "text='🔙', normalized='🔙', callback='captchab_signin_...'"
]
```

For `value=33`, the correct click sequence is `➖`, `➖`, `🍋`.

During GitHub Actions debugging, keep command output visible. Do not redirect
`telegram-signer ... run-force` output to `/dev/null`, otherwise the real button
text and callback data will be hidden.
## LLM Configuration

LLM-backed actions read configuration from either environment variables or the
workdir config file created by `llm-config`.

Environment variables:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

Persistent workdir file:

```text
<workdir>/.openai_config.json
```

Do not commit sessions, session strings, `.env` files, `.openai_config.json`, logs,
or local SQLite databases.

