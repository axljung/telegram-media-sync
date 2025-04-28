#!/usr/bin/env python3
"""
Script: telegram_media_sync.py

Python version using Telethon:
- Displays all chats/channels for selection via an interactive CLI menu using questionary (synchronous via telethon.sync)
- Downloads only new media files (synchronization via locally stored message IDs per channel)
- Persists authentication using a Telethon session

Requirements:
  - Telethon (`pip install telethon`)
  - questionary (`pip install questionary`)
  - Telegram API ID and API Hash (from https://my.telegram.org)

Usage Examples:
  # Interactive selection of chats/channels:
  python telegram_media_sync.py \
      --api-id YOUR_API_ID \
      --api-hash YOUR_API_HASH \
      --list-chats \
      --output-dir /path/to/downloads \
      [--session SESSION_NAME]

  # Specify channel by username or ID directly:
  python telegram_media_sync.py \
      --api-id YOUR_API_ID \
      --api-hash YOUR_API_HASH \
      --channel CHANNEL_USERNAME_OR_ID \
      --output-dir /path/to/downloads \
      [--session SESSION_NAME] \
      [--limit 1000]

If neither --channel nor --list-chats is provided, the script will exit.
"""
import os
import argparse
import asyncio
from telethon import TelegramClient, errors
from telethon.sync import TelegramClient as SyncTelegramClient
import questionary


def choose_dialog_sync(api_id, api_hash, session_name):
    """
    Synchronously list all chats/channels and let the user select one via questionary.
    """
    with SyncTelegramClient(session_name, api_id, api_hash) as client:
        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(client.phone)
            code = questionary.text("Enter the Telegram authentication code: ").ask()
            client.sign_in(client.phone, code)
        dialogs = client.get_dialogs()
    choices = []
    for dialog in dialogs:
        entity = dialog.entity
        name = getattr(entity, 'title', None) or getattr(entity, 'username', None) or getattr(entity, 'first_name', '')
        choices.append(f"{name} ({entity.id})")

    choice = questionary.select(
        "Select a chat/channel:",
        choices=choices
    ).ask()
    if choice is None:
        return None
    idx = choices.index(choice)
    return dialogs[idx].entity

async def download_media(client, target, output_dir, limit=None):
    # Resolve the entity and channel ID
    entity = await client.get_entity(target)
    channel_id = entity.id
    # Create a directory for this channel
    channel_dir = os.path.join(output_dir, str(channel_id))
    os.makedirs(channel_dir, exist_ok=True)
    # File to track downloaded message IDs
    record_file = os.path.join(channel_dir, '.downloaded_ids.txt')
    downloaded_ids = set()
    if os.path.exists(record_file):
        with open(record_file, 'r') as rf:
            downloaded_ids = {int(line.strip()) for line in rf if line.strip().isdigit()}
    # Gather existing files to avoid duplicates based on filename prefix
    existing_files = os.listdir(channel_dir)

    record_fp = open(record_file, 'a')

    print(f"Starting download for channel ID {channel_id} into {channel_dir}...")
    count = 0
    async for message in client.iter_messages(entity, limit=limit):
        # Skip messages without media
        if not message.media:
            continue
        # Skip if message ID recorded
        if message.id in downloaded_ids:
            print(f"[SKIP] Message {message.id} already downloaded (recorded).")
            continue
        # Skip if a file for this message ID already exists
        file_exists = any(f.startswith(f"{message.id}.") or f == str(message.id) for f in existing_files)
        if file_exists:
            print(f"[SKIP] File for message {message.id} already exists.")
            downloaded_ids.add(message.id)
            record_fp.write(f"{message.id}")
            continue
        try:
            path = await client.download_media(message, file=channel_dir)
            count += 1
            print(f"[{count}] Saved: {path}")
            record_fp.write(f"{message.id}")
            downloaded_ids.add(message.id)
            # Update existing_files for subsequent checks
            existing_files.append(os.path.basename(path))
        except errors.FloodWaitError as e:
            print(f"Rate limit reached, waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            path = await client.download_media(message, file=channel_dir)
            count += 1
            print(f"[{count}] Saved after wait: {path}")
            record_fp.write(f"{message.id}")
            downloaded_ids.add(message.id)
            existing_files.append(os.path.basename(path))
        except Exception as e:
            print(f"Error downloading message {message.id}: {e}")
    record_fp.close()
    print(f"Done. Total new files downloaded: {count}")

async def main(api_id, api_hash, channel, output_dir, limit, session_name):
    # Initialize Telethon client with persistent session
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"Logged in as: {getattr(me, 'first_name', None) or getattr(me, 'username', '')}")

    # Download media from the specified target
    await download_media(client, channel, output_dir, limit)
    await client.disconnect()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Synchronously download Telegram media per channel')
    parser.add_argument('--api-id', type=int, required=True, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, required=True, help='Telegram API Hash')
    parser.add_argument('--session', type=str, default='media_sync', help='Telethon session name for persistent login')
    parser.add_argument('--channel', type=str, help='Username or ID of the channel')
    parser.add_argument('--list-chats', action='store_true', help='List all chats/channels for selection')
    parser.add_argument('--output-dir', type=str, default='downloads', help='Base directory to save media')
    parser.add_argument('--limit', type=int, help='Maximum number of messages to scan (default: all)')
    args = parser.parse_args()

    if not args.channel and not args.list_chats:
        parser.error('Either --channel or --list-chats must be provided.')

    target = args.channel
    if args.list_chats:
        entity = choose_dialog_sync(args.api_id, args.api_hash, args.session)
        if entity is None:
            print("Operation cancelled.")
            exit(1)
        target = entity

    asyncio.run(main(
        api_id=args.api_id,
        api_hash=args.api_hash,
        channel=target,
        output_dir=args.output_dir,
        limit=args.limit,
        session_name=args.session
    ))
