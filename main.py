import os
import logging
import sys
import asyncio
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

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LicioGelliFinBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message with inline keyboard when /start command is issued."""
        keyboard = [
            [
                InlineKeyboardButton("🎵 tidal-dl-ng", callback_data='tidal_dl_ng'),
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
            "🎵 *tidal-dl-ng* - Per scaricare musica da Tidal\n"
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
            'tidal_dl_ng': (
                "🎵 *Hai selezionato tidal-dl-ng!*\n\n"
                "Ora puoi inviare un link di Tidal per scaricare:\n"
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
        
        # Add back button for help
        if query.data in ['help']:
            keyboard = [[InlineKeyboardButton("« Torna al menu", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        elif query.data == 'back_to_menu':
            await self.show_main_menu(query)
            return
        else:
            # For tool selection, add a back button
            keyboard = [[InlineKeyboardButton("« Torna al menu", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            response,
            reply_markup=reply_markup if query.data != 'back_to_menu' else None,
            parse_mode='Markdown'
        )
    
    async def show_main_menu(self, query):
        """Show the main menu."""
        keyboard = [
            [
                InlineKeyboardButton("🎵 tidal-dl-ng", callback_data='tidal_dl_ng'),
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

    def is_tidal_url(self, url: str) -> bool:
        """Check if the URL is from Tidal."""
        return 'tidal.com' in url.lower()

    async def download_with_tidal_dl_ng(self, url: str) -> tuple[bool, str]:
        """Download using tidal-dl-ng and return (success, message)."""
        try:
            # Run tidal-dl-ng command
            process = await asyncio.create_subprocess_exec(
                'tidal-dl-ng',
                'dl',
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Success
                output = stdout.decode('utf-8').strip()
                return True, f"✅ Download completato con successo!"
            else:
                # Error
                error_output = stderr.decode('utf-8').strip()
                logger.error(f"tidal-dl-ng failed with return code {process.returncode}: {error_output}")
                return False, f"❌ Errore durante il download:\n\n`{error_output[-500:]}`"
                
        except FileNotFoundError:
            logger.error("tidal-dl-ng not found in system PATH")
            return False, "❌ tidal-dl-ng non trovato. Assicurati che sia installato e nel PATH."
        except Exception as e:
            logger.error(f"Unexpected error during tidal-dl-ng execution: {e}")
            return False, f"❌ Errore imprevisto: {str(e)}"

    async def download_with_yt_dlp(self, url: str) -> tuple[bool, str]:
        """Download using yt-dlp and return (success, message)."""
        try:
            # Run yt-dlp command
            process = await asyncio.create_subprocess_exec(
                'yt-dlp',
                '--paths', '~/Media/to_sort',
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
                output = stdout.decode('utf-8').strip()
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
        
        # Check if it's a Tidal URL
        if self.is_tidal_url(url):
            if url.endswith("/u"):
                url = url[:-2]

            # Send processing message
            processing_msg = await update.message.reply_text(
                "⏳ Avvio download con tidal-dl-ng...\n"
                "Questo potrebbe richiedere alcuni minuti."
            )
            
            try:
                # Download with tidal-dl-ng
                success, message = await self.download_with_tidal_dl_ng(url)
                
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
        else:
            # Use yt-dlp for non-Tidal URLs
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