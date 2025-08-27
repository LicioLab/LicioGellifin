import asyncio
import telegram
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")
sav_chat_id = os.getenv("SAV_CHAT_ID")

async def main():
    bot = telegram.Bot(token)
    async with bot:
        testo = subprocess.run(["ls", "-l", "."], capture_output=True, text=True)
        await bot.send_message(chat_id=sav_chat_id, text=testo.stdout)


if __name__ == '__main__':
    asyncio.run(main())
