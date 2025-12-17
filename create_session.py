import os
from telethon import TelegramClient
import asyncio

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_NAME = "server_session"  # назва сесії у контейнері

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def main():
    await client.start()  # тут запустить логін через код, якщо потрібно
    print(f"Session {SESSION_NAME}.session created!")

asyncio.run(main())
