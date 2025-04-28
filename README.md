# Telegram Media Sync

A Python CLI tool to download all new media from a Telegram chat or channel, with persistent authentication, per-channel folders, and an interactive selection menu.

## Features

- **Interactive Selection**: Choose from all your chats and channels via a nice CLI menu powered by `questionary`.
- **Persistent Session**: Login once; session data is saved so you don't need to re-authenticate every run.
- **Per-Channel Storage**: Media are organized into subdirectories named by channel ID.
- **Sync Mode**: Skips already-downloaded files to avoid duplicates.

## Prerequisites

- Python 3.8 or higher
- A Telegram API ID and API Hash (obtain from https://my.telegram.org)

## Installation

```bash
# Clone the repository
git clone https://github.com/axljung/telegram-media-sync.git
cd telegram-media-sync

# Create and activate a virtual environment (Unix/macOS)
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
env\Scripts\Activate.ps1

# Install required Python packages
pip install telethon questionary
```

> Optionally, you can save dependencies to a `requirements.txt`:
>
> ```bash
> pip freeze > requirements.txt
> ```

## Usage

```bash
# Interactive mode: list chats and choose one
python telegram_media_sync.py \
  --api-id YOUR_API_ID \
  --api-hash YOUR_API_HASH \
  --list-chats \
  --output-dir ./downloads \
  --session media_session

# Direct mode: specify channel by username or ID
python telegram_media_sync.py \
  --api-id YOUR_API_ID \
  --api-hash YOUR_API_HASH \
  --channel my_channel_username \
  --output-dir ./downloads \
  --session media_session \
  --limit 500
```

### Command-line Arguments

| Argument      | Type    | Required | Default         | Description                                        |
|---------------|---------|----------|-----------------|----------------------------------------------------|
| `--api-id`    | int     | yes      |                 | Your Telegram API ID                               |
| `--api-hash`  | string  | yes      |                 | Your Telegram API Hash                             |
| `--session`   | string  | no       | `media_sync`    | Name for the Telethon session file                 |
| `--list-chats`| flag    | no       |                 | If set, displays an interactive menu of dialogs    |
| `--channel`   | string  | no       |                 | Channel username or numeric ID (e.g. `-100123456...`)|
| `--output-dir`| string  | no       | `downloads`     | Base directory where media will be stored          |
| `--limit`     | int     | no       | all messages    | Maximum number of messages to scan                 |

> **Note:** Either `--list-chats` or `--channel` must be provided.

## First Run

On the first invocation, Telethon will prompt for your phone number and an authentication code sent by Telegram. Once verified, a session file (`<session>.session`) is created, and subsequent runs will use it.

## Folder Structure

```
downloads/            # base output directory
└── <channel_id>/     # one folder per channel
    ├── .downloaded_ids.txt  # recorded message IDs
    ├── 12345.jpg            # downloaded media files
    └── 67890.mp4
```

## License

This project is released under the MIT License. Feel free to use and adapt it as you like.

