# telegram-signer

## 繁體中文

`telegram-signer` 是一個面向 Telegram 自動簽到的 Python CLI 工具。它可以按照設定時間向指定聊天或機器人發送簽到訊息、點擊行內鍵盤按鈕、處理 Telegram 話題 ID、保存 SQLite 簽到記錄，並可選擇使用 OpenAI 相容 API 處理圖片或計算類驗證。

本專案改編自並基於 [amchii/tg-signer](https://github.com/amchii/tg-signer)。感謝原專案提供的簽到流程、設定結構和 Telegram 自動化基礎。本版本在此基礎上做了更偏向公開發佈和 GitHub Actions 使用的整理。

### 精簡內容

- 聚焦 Telegram 簽到 CLI，不包含額外的面板或長期監聽功能。
- 公開倉庫和 PyPI 套件只保留可執行源碼、README、CHANGELOG、LICENSE、測試和必要打包設定。
- 不包含個人 `config.json`、session、token、`.env`、本地資料庫、GitHub Actions 私人工作流或其他隱私檔案。
- 保留舊版設定相容邏輯，方便從原有設定逐步遷移。

### 新增與改進

- 提供 `telegram-signer` 命令，可直接透過 PyPI 安裝。
- 支援 `--session-string` 和 `--in-memory`，更適合 GitHub Actions Secrets 使用。
- 命令格式要求明確指定帳號，例如 `telegram-signer account_a run task_name`，多帳號任務更清楚。
- 支援 `run-force`，可在 GitHub Actions 中立即執行一次任務。
- 使用 SQLite 保存簽到記錄，並支援從舊的 `sign_record.json` 延遲遷移。
- 支援 Telegram forum topic 的 `message_thread_id`。
- 支援文字發送、骰子發送、按鈕點擊、圖片選項識別、計算題回覆和老虎機驗證碼按鈕解答。
- 老虎機驗證碼支援 Telegram 兩段式流程：先收到老虎機結果，再收到「您在老虎機中看到了哪些表情符號？」的按鈕訊息。
- 針對老虎機按鈕做了兼容：`➖` 會被視為 BAR，`🍇` 是葡萄，`🍋` 是檸檬，`7️⃣` 是數字 7，`🔙` 是返回鍵且不會被當作 BAR。
- 保留診斷日誌，方便在 GitHub Actions 中查看按鈕文字、正規化文字和 callback data。

### 優點

- 安裝簡單：`pip install -U telegram-signer`。
- 更適合自動化：GitHub Actions 可以直接從 Secrets 注入 session 和任務設定。
- 更乾淨：公開發佈內容和私人設定分離，降低誤上傳隱私資料的風險。
- 更容易除錯：老虎機驗證碼和按鈕流程會輸出清楚的診斷資訊。
- 更容易維護：README、CHANGELOG、版本號和 PyPI 包資訊集中在乾淨發佈目錄中。

### 安裝

需要 Python 3.10 或更新版本。

```sh
pip install -U telegram-signer
```

### 常用命令

帳號名稱必須放在子命令之前：

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

全域選項必須放在帳號名稱之前：

```sh
telegram-signer --workdir .signer account_a run task_name
```

### 設定路徑

預設任務設定路徑：

```text
<workdir>/telegram-signer/config/<task_name>/config.json
```

舊版路徑仍可讀取，載入後會複製到新路徑：

```text
<workdir>/signs/<task_name>/config.json
```

簽到記錄使用 SQLite：

```text
<workdir>/data.sqlite3
```

### 設定範例

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

Action ID：

| ID | 動作 |
| --- | --- |
| 1 | 發送文字 |
| 2 | 發送骰子 |
| 3 | 按文字點擊鍵盤按鈕 |
| 4 | 使用 LLM 根據圖片選擇選項 |
| 5 | 使用 LLM 回覆計算題 |
| 6 | 在 `if_*` 條件匹配時解答老虎機驗證碼按鈕 |

老虎機驗證碼建議至少加入一個條件：

```json
{"action": 6, "if_dice_emoji": "🎰"}
{"action": 6, "if_text": "老虎機"}
{"action": 6, "if_regex": "slot|captcha|verification|老虎機"}
```

### LLM 設定

LLM 動作可讀取環境變數：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

也可以使用 `llm-config` 生成工作目錄設定：

```text
<workdir>/.openai_config.json
```

請不要提交 session、session string、`.env`、`.openai_config.json`、日誌或本地 SQLite 資料庫。

## 简体中文

`telegram-signer` 是一个面向 Telegram 自动签到的 Python CLI 工具。它可以按照设定时间向指定聊天或机器人发送签到消息、点击行内键盘按钮、处理 Telegram 话题 ID、保存 SQLite 签到记录，并可选择使用 OpenAI 兼容 API 处理图片或计算类验证。

本项目改编自并基于 [amchii/tg-signer](https://github.com/amchii/tg-signer)。感谢原项目提供的签到流程、配置结构和 Telegram 自动化基础。本版本在此基础上做了更偏向公开发布和 GitHub Actions 使用的整理。

### 精简内容

- 聚焦 Telegram 签到 CLI，不包含额外面板或长期监听功能。
- 公开仓库和 PyPI 包只保留可执行源码、README、CHANGELOG、LICENSE、测试和必要打包配置。
- 不包含个人 `config.json`、session、token、`.env`、本地数据库、GitHub Actions 私人工作流或其他隐私文件。
- 保留旧版配置兼容逻辑，方便从原有配置逐步迁移。

### 新增与改进

- 提供 `telegram-signer` 命令，可直接通过 PyPI 安装。
- 支持 `--session-string` 和 `--in-memory`，更适合 GitHub Actions Secrets 使用。
- 命令格式要求明确指定账号，例如 `telegram-signer account_a run task_name`，多账号任务更清楚。
- 支持 `run-force`，可在 GitHub Actions 中立即执行一次任务。
- 使用 SQLite 保存签到记录，并支持从旧的 `sign_record.json` 延迟迁移。
- 支持 Telegram forum topic 的 `message_thread_id`。
- 支持文字发送、骰子发送、按钮点击、图片选项识别、计算题回复和老虎机验证码按钮解答。
- 老虎机验证码支持 Telegram 两段式流程：先收到老虎机结果，再收到“您在老虎机中看到了哪些表情符号？”的按钮消息。
- 针对老虎机按钮做了兼容：`➖` 会被视为 BAR，`🍇` 是葡萄，`🍋` 是柠檬，`7️⃣` 是数字 7，`🔙` 是返回键且不会被当作 BAR。
- 保留诊断日志，方便在 GitHub Actions 中查看按钮文字、规范化文字和 callback data。

### 优点

- 安装简单：`pip install -U telegram-signer`。
- 更适合自动化：GitHub Actions 可以直接从 Secrets 注入 session 和任务配置。
- 更干净：公开发布内容和私人配置分离，降低误上传隐私资料的风险。
- 更容易调试：老虎机验证码和按钮流程会输出清楚的诊断信息。
- 更容易维护：README、CHANGELOG、版本号和 PyPI 包信息集中在干净发布目录中。

### 安装

需要 Python 3.10 或更新版本。

```sh
pip install -U telegram-signer
```

### 常用命令

账号名称必须放在子命令之前：

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

全局选项必须放在账号名称之前：

```sh
telegram-signer --workdir .signer account_a run task_name
```

### 配置路径

默认任务配置路径：

```text
<workdir>/telegram-signer/config/<task_name>/config.json
```

旧版路径仍可读取，加载后会复制到新路径：

```text
<workdir>/signs/<task_name>/config.json
```

签到记录使用 SQLite：

```text
<workdir>/data.sqlite3
```

### 配置示例

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

Action ID：

| ID | 动作 |
| --- | --- |
| 1 | 发送文字 |
| 2 | 发送骰子 |
| 3 | 按文字点击键盘按钮 |
| 4 | 使用 LLM 根据图片选择选项 |
| 5 | 使用 LLM 回复计算题 |
| 6 | 在 `if_*` 条件匹配时解答老虎机验证码按钮 |

老虎机验证码建议至少加入一个条件：

```json
{"action": 6, "if_dice_emoji": "🎰"}
{"action": 6, "if_text": "老虎机"}
{"action": 6, "if_regex": "slot|captcha|verification|老虎机"}
```

### LLM 设置

LLM 动作可读取环境变量：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

也可以使用 `llm-config` 生成工作目录配置：

```text
<workdir>/.openai_config.json
```

请不要提交 session、session string、`.env`、`.openai_config.json`、日志或本地 SQLite 数据库。

## English

`telegram-signer` is a Python CLI tool for automated Telegram check-ins. It can send configured check-in messages, click inline keyboard buttons, handle Telegram topic IDs, keep SQLite check-in records, and optionally use an OpenAI-compatible API for image or calculation-style verification steps.

This project is adapted from and based on [amchii/tg-signer](https://github.com/amchii/tg-signer). Thanks to the original project for the check-in flow, configuration structure, and Telegram automation foundation. This version focuses on a cleaner public package and a GitHub Actions friendly workflow.

### What Was Simplified

- Focuses on the Telegram check-in CLI and does not include extra dashboard or long-running watcher features.
- The public repository and PyPI package keep only runnable source code, README, CHANGELOG, LICENSE, tests, and required packaging files.
- Personal `config.json`, sessions, tokens, `.env` files, local databases, private GitHub Actions workflows, and other private files are not included.
- Legacy config compatibility is kept so existing setups can migrate gradually.

### Added And Improved

- Provides the `telegram-signer` command through PyPI installation.
- Supports `--session-string` and `--in-memory`, which works well with GitHub Actions Secrets.
- Requires an explicit account name, such as `telegram-signer account_a run task_name`, making multi-account usage clearer.
- Adds `run-force` for one-shot execution in GitHub Actions.
- Stores check-in records in SQLite and supports lazy migration from old `sign_record.json` files.
- Supports Telegram forum topic `message_thread_id`.
- Supports sending text, sending dice, clicking buttons, choosing image options with an LLM, replying to calculation prompts, and solving slot-machine captcha buttons.
- Supports the two-message Telegram slot-machine flow: first receiving the dice result, then receiving the prompt asking which symbols were shown.
- Handles observed slot-machine buttons: `➖` means BAR, `🍇` means grapes, `🍋` means lemon, `7️⃣` means seven, and `🔙` is a back button that is never used as BAR.
- Keeps diagnostic logs for button text, normalized text, and callback data, which helps GitHub Actions debugging.

### Advantages

- Easy installation: `pip install -U telegram-signer`.
- Automation friendly: GitHub Actions can inject sessions and task configuration through Secrets.
- Cleaner release contents: public source and private configuration are separated to reduce accidental leaks.
- Easier debugging: slot-machine captcha and button flows expose clear diagnostic information.
- Easier maintenance: README, CHANGELOG, version metadata, and PyPI package metadata live in the clean release directory.

### Installation

Python 3.10 or newer is required.

```sh
pip install -U telegram-signer
```

### Common Commands

The account name is required before the command:

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

### Config Paths

Default task config path:

```text
<workdir>/telegram-signer/config/<task_name>/config.json
```

The old path is still readable and is copied to the new path when loaded:

```text
<workdir>/signs/<task_name>/config.json
```

Check-in records use SQLite:

```text
<workdir>/data.sqlite3
```

### Example Config

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
| 3 | click a keyboard button by text |
| 4 | choose an image option with an LLM |
| 5 | reply to a calculation prompt with an LLM |
| 6 | solve slot-machine captcha buttons when an `if_*` condition matches |

Slot-machine captcha solving should include at least one condition:

```json
{"action": 6, "if_dice_emoji": "🎰"}
{"action": 6, "if_text": "slot"}
{"action": 6, "if_regex": "slot|captcha|verification"}
```

### LLM Configuration

LLM actions can read environment variables:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

They can also use the workdir config file created by `llm-config`:

```text
<workdir>/.openai_config.json
```

Do not commit sessions, session strings, `.env` files, `.openai_config.json`, logs, or local SQLite databases.
