

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

YT_DEST_PATH = /media/licio/Archivio/Media/to_sort

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
                InlineKeyboardButton("🎵 qobuz-dl", callback_data='qobuz-dl'),
                InlineKeyboardButton("📺 yt-dlp", callback_data='yt_dlp'),
            ],
            [
                InlineKeyboardButton("📁 List Files", callback_data='list_files'),
                InlineKeyboardButton("❓ Help", callback_data='help'),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            "🤖 *Benvenuto in LicioGelliFin Bot!*\n\n"
            "Seleziona il tool che vuoi utilizzare per scaricare contenuti multimediali:\n\n"
            "🎵 *qobuz-dl* - Per scaricare musica da Qobuz\n"
            "📺 *yt-dlp* - Per scaricare video da YouTube e altri siti\n"
            "📁 *List Files* - Mostra i file nella cartella corrente\n\n"
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
            "/list - Mostra i file nella cartella corrente\n"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def list_files(self) -> tuple[bool, str]:
        """List files in current directory using ls command."""
        try:
            # Run ls command
            process = await asyncio.create_subprocess_exec(
                'ls',
                #'-l',
                '/Users/orald/Media/Music',  # Long format with hidden files
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Success
                output = stdout.decode('utf-8').strip()
                if not output:
                    return True, "📁 La cartella è vuota."
                
                # Limit output length for Telegram message limits
                if len(output) > 3000:
                    output = output[:3000] + "\n\n... (output truncated)"
                
                return True, f"📁 *File nella cartella corrente:*\n\n```\n{output}\n```"
            else:
                # Error
                error_output = stderr.decode('utf-8').strip()
                logger.error(f"ls command failed with return code {process.returncode}: {error_output}")
                return False, f"❌ Errore durante l'esecuzione del comando ls:\n\n`{error_output}`"
                
        except FileNotFoundError:
            logger.error("ls command not found in system PATH")
            return False, "❌ Comando ls non trovato. Sistema non supportato."
        except Exception as e:
            logger.error(f"Unexpected error during ls execution: {e}")
            return False, f"❌ Errore imprevisto: {str(e)}"

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button presses."""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'list_files':
            # Show loading message
            await query.edit_message_text(
                "⏳ Caricamento lista file...",
                parse_mode='Markdown'
            )
            
            # Get file list
            success, message = await self.list_files()
            
            # Add back button
            keyboard = [[InlineKeyboardButton("« Torna al menu", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
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
                InlineKeyboardButton("📁 List Files", callback_data='list_files'),
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

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /list command."""
        processing_msg = await update.message.reply_text("⏳ Caricamento lista file...")
        
        success, message = await self.list_files()
        
        await processing_msg.edit_text(
            message,
            parse_mode='Markdown'
        )

    def is_qobuz_url(self, url: str) -> bool:
        """Check if the URL is from qobuz."""
        return 'qobuz.com' in url.lower()

    def parse_progress_line(self, line: str, progress_data: dict) -> None:
        """Parse progress information from qobuz-dl output lines."""
        
        # Match overall list progress (e.g., "List 'Fastidio' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%")
        list_match = re.search(r"List\s+'[^']+'\s+[━═-]+\s+(\d+)%", line)
        if list_match:
            progress_data['overall_progress'] = int(list_match.group(1))
            return
        
        # Match individual track progress (e.g., "Item 'Kaos - Intro' ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%")
        track_match = re.search(r"Item\s+'([^']+)'\s+[━═-]+\s+(\d+)%", line)
        if track_match:
            track_name = track_match.group(1)
            track_progress = int(track_match.group(2))
            
            # If this is a new track starting
            if progress_data['current_track'] != track_name:
                progress_data['current_track'] = track_name
                progress_data['completed_tracks'] += 1
            
            progress_data['track_progress'] = track_progress
            return
        
        # Match track count from "Finished list" or similar lines
        finished_match = re.search(r"Finished list\s+'[^']+'.*?(\d+)\s+tracks?", line, re.IGNORECASE)
        if finished_match:
            progress_data['total_tracks'] = int(finished_match.group(1))
            return
        
        # Estimate total tracks from download messages
        if "Downloaded item" in line and progress_data['total_tracks'] == 0:
            progress_data['total_tracks'] = progress_data.get('total_tracks', 0) + 1

    def format_progress_message(self, progress_data: dict) -> str:
        """Format progress information for Telegram message."""
        lines = []
        
        # Add overall progress
        if progress_data['overall_progress'] > 0:
            lines.append(f"📊 Overall Progress: {progress_data['overall_progress']}%")
        
        # Add current track progress
        if progress_data['current_track']:
            lines.append(f"🎵 Current Track: {progress_data['current_track']}")
            lines.append(f"📈 Track Progress: {progress_data['track_progress']}%")
        
        # Add track count information
        if progress_data['total_tracks'] > 0:
            lines.append(
                f"📋 Tracks: {progress_data['completed_tracks']}/{progress_data['total_tracks']} "
                f"({progress_data['completed_tracks']/progress_data['total_tracks']*100:.1f}%)"
            )
        
        # Add loading indicator if no specific progress available
        if not lines:
            lines.append("⏳ Download in progress...")
        
        return "\n".join(lines)

    async def download_with_qobuz_dl(self, url: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
        """Download using qobuz-dl with real-time progress updates."""
        try:
            # Send initial processing message
            processing_msg = await update.message.reply_text(
                "⏳ Starting download with qobuz-dl...\n"
                "Progress: 0%"
            )
            
            # Create subprocess with stdout/stderr pipes
            process = await asyncio.create_subprocess_exec(
                '/home/licio/.pyenv/shims/qobuz-dl',
                'dl',
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Variables to track progress
            last_update_time = 0
            progress_data = {
                'current_track': None,
                'track_progress': 0,
                'overall_progress': 0,
                'total_tracks': 0,
                'completed_tracks': 0
            }
            
            # Read output line by line
            while True:
                # Read line from stdout
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_text = line.decode('utf-8').strip()
                
                # Parse progress information
                self.parse_progress_line(line_text, progress_data)
                
                # Update message periodically (max every 5 seconds)
                current_time = time.time()
                if current_time - last_update_time >= 5 or progress_data['overall_progress'] == 100:
                    progress_text = self.format_progress_message(progress_data)
                    try:
                        await processing_msg.edit_text(progress_text)
                        last_update_time = current_time
                    except Exception as e:
                        logger.error(f"Error updating progress message: {e}")
            
            # Wait for process completion
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, "✅ Download completed successfully!"
            else:
                error_output = stderr.decode('utf-8').strip()
                logger.error(f"qobuz-dl failed with return code {process.returncode}: {error_output}")
                return False, f"❌ Errore durante il download:\n\n`{error_output[-500:]}`"
                
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
        self.application.add_handler(CommandHandler("list", self.list_command))
        
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