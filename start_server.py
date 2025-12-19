import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from server import app, start_client
import os

async def main():
    await start_client()
    config = Config()
    config.bind = [f"0.0.0.0:{os.environ.get('PORT', 5000)}"]
    config.debug = True
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())
