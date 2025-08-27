import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import os
from dotenv import load_dotenv

# carica il file .env
load_dotenv()

# accedi alle variabili
token = os.getenv("TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # esegue il comando in modo async
    proc = await asyncio.create_subprocess_exec(
        "ls", "-l", ".",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    output = stdout.decode().strip()
    errors = stderr.decode().strip()

    # prepara il messaggio
    msg = output if output else "Nessun output"
    if errors:
        msg += f"\n\nErrori:\n{errors}"

    # invia la risposta direttamente alla chat che ha scritto /start
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()
