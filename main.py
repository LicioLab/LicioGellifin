import os
import logging
import sys
import asyncio
import re
import time
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler,
    ContextTypes,
    filters
)

YT_DEST_PATH = "/media/licio/multimedia/to_sort"

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Nota: Rimuovi questa riga se vuoi vedere i log di errore di connessione (utile per debug)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class LicioGelliFinBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message with inline keyboard when /start command is issued."""
        keyboard = [
            [
                InlineKeyboardButton("🎵 qobuz-dl", callback_data='qobuz-dl'),
                InlineKeyboardButton("📺 yt-dlp", callback_data='yt_dlp'),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data='help'),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            "🤖 *Benvenuto in LicioGelliFin Bot!*\n\n"
            "Seleziona il tool che vuoi utilizzare per scaricare contenuti multimediali:\n\n"
            "🎵 *qobuz-dl* - Per scaricare musica da Qobuz\n"
            "📺 *yt-dlp* - Per scaricare video da YouTube e altri siti\n\n"
            "Usa /help per maggiori informazioni."
        )
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send help information."""
        help_text = (
            "🔧 *Comandi disponibili:*\n\n"
            "/start - Avvia il bot e mostra le opzioni di download\n"
            "/dl - Mostra le opzioni di download, alias per /start\n"
            "/help - Mostra questo messaggio di aiuto\n"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button presses."""
        query = update.callback_query
        await query.answer()
        
        responses = {
            'qobuz-dl': (
                "🎵 *Hai selezionato qobuz-dl!*\n\n"
                "Ora puoi inviare un link di Qobuz per scaricare:\n"
                "• Album completi\n"
                "• Singole tracce\n"
                "• Playlist\n\n"
                "Invia il link per iniziare il download!"
            ),
            'yt_dlp': (
                "📺 *Hai selezionato yt-dlp!*\n\n"
                "Ora puoi inviare un link per scaricare da:\n"
                "• YouTube\n"
                "• Vimeo\n"
                "• SoundCloud\n"
                "• E molti altri siti!\n\n"
                "Invia il link per iniziare il download!"
            ),
            'help': (
                "❓ *Serve aiuto?*\n\n"
                "Usa il comando /help per vedere tutti i comandi disponibili "
                "e le istruzioni dettagliate su come utilizzare il bot."
            )
        }
        
        response = responses.get(query.data, "Opzione non riconosciuta!")
        
        # Add back button for help and tool selection
        if query.data in ['help', 'qobuz-dl', 'yt_dlp']:
            keyboard = [[InlineKeyboardButton("« Torna al menu", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        elif query.data == 'back_to_menu':
            await self.show_main_menu(query)
            return
        else:
            reply_markup = None
        
        await query.edit_message_text(
            response,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_main_menu(self, query):
        """Show the main menu."""
        keyboard = [
            [
                InlineKeyboardButton("🎵 qobuz-dl", callback_data='qobuz-dl'),
                InlineKeyboardButton("📺 yt-dlp", callback_data='yt_dlp'),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data='help'),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            "🤖 *Benvenuto in LicioGelliFin Bot!*\n\n"
            "Seleziona il tool che vuoi utilizzare:"
        )
        
        await query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def is_qobuz_url(self, url: str) -> bool:
        """Check if the URL is from qobuz."""
        return 'qobuz.com' in url.lower()

    async def download_with_qobuz_dl(self, url: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
        """Download using qobuz-dl without progress bar."""
        try:
            # Avvisa l'utente che il download è partito
            await update.message.reply_text(
                "⏳ Download avviato con qobuz-dl... Ti avviserò quando sarà finito."
            )

            name = update.message.from_user.first_name
            msg = f"{name} is downloading {url}"
            logger.info(msg)
            
            # Crea il sottoprocesso ed esegui il comando
            process = await asyncio.create_subprocess_exec(
                '/home/licio/.pyenv/shims/qobuz-dl',
                'dl',
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Attende la fine del processo catturando l'output (wait implicit)
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, "✅ Download completato con successo!"
            else:
                # Decodifica l'errore per i log
                error_msg = stderr.decode('utf-8', errors='replace').strip()
                logger.error(f"qobuz-dl failed with return code {process.returncode}: {error_msg}")
                return False, f"❌ Errore durante il download (Codice {process.returncode})."
                
        except FileNotFoundError:
            logger.error("qobuz-dl not found in system PATH")
            return False, "❌ qobuz-dl non trovato. Assicurati che sia installato e nel PATH."
        except Exception as e:
            logger.error(f"Unexpected error during qobuz-dl execution: {e}")
            return False, f"❌ Errore imprevisto: {str(e)}"

    async def download_with_yt_dlp(self, url: str) -> tuple[bool, str]:
        """Download using yt-dlp and return (success, message)."""
        try:
            # Run yt-dlp command
            process = await asyncio.create_subprocess_exec(
                'yt-dlp',
                '--paths', YT_DEST_PATH,
                '--yes-playlist',
                '--format', 'bestaudio',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Success
                return True, f"✅ Download completato con successo!"
            else:
                # Error
                error_output = stderr.decode('utf-8').strip()
                logger.error(f"yt-dlp failed with return code {process.returncode}: {error_output}")
                return False, f"❌ Errore durante il download:\n\n`{error_output[-500:]}`"
                
        except FileNotFoundError:
            logger.error("yt-dlp not found in system PATH")
            return False, "❌ yt-dlp non trovato. Assicurati che sia installato e nel PATH."
        except Exception as e:
            logger.error(f"Unexpected error during yt-dlp execution: {e}")
            return False, f"❌ Errore imprevisto: {str(e)}"

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle URL messages for downloading."""
        url = update.message.text.strip()
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text(
                "❌ Per favore invia un URL valido che inizi con http:// o https://"
            )
            return
        
        # Check if it's a qobuz URL
        if self.is_qobuz_url(url):
            if url.endswith("/u"):
                url = url[:-2]

            try:
                # Download with qobuz-dl (now with progress updates)
                success, message = await self.download_with_qobuz_dl(url, update, context)
                
                # Send final result
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                await update.message.reply_text(
                    "❌ Si è verificato un errore durante l'elaborazione del link.\n"
                    f"Dettagli: {str(e)}"
                )
        else:
            # Use yt-dlp for non-Qobuz URLs
            processing_msg = await update.message.reply_text(
                "⏳ Avvio download con yt-dlp...\n"
                "Questo potrebbe richiedere alcuni minuti."
            )
            
            try:
                # Download with yt-dlp
                success, message = await self.download_with_yt_dlp(url)
                
                await processing_msg.edit_text(
                    message,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                await processing_msg.edit_text(
                    "❌ Si è verificato un errore durante l'elaborazione del link.\n"
                    f"Dettagli: {str(e)}"
                )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)
        
        # Notify user of error (optional)
        if update.message:
            await update.message.reply_text(
                "❌ Si è verificato un errore imprevisto.\n"
                "L'errore è stato registrato e verrà risolto presto."
            )

    def setup_handlers(self):
        """Setup all bot handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("dl", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        # Removed /list command handler
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handler for URLs
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)

    def run(self):
        """Start the bot."""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable not found!")
            sys.exit(1)
        
        # Create the Application
        self.application = Application.builder().token(self.token).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Run the bot
        logger.info("🚀 LicioGelliFin Bot is starting...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main() -> None:
    """Main function."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not found!")
        logger.error("Please create a .env file with your bot token:")
        logger.error("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        sys.exit(1)
    
    bot = LicioGelliFinBot(token)
    bot.run()

if __name__ == '__main__':
    main()
