"""
Telegram notifier for scraper notifications.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional
import threading

from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram bot."""
    
    def __init__(self, bot_token: str, chat_id: str):
        if not bot_token or bot_token == "TU_BOT_TOKEN_AQUI":
            raise ValueError("Invalid bot token")
        
        if not chat_id or chat_id == "TU_CHAT_ID_AQUI":
            raise ValueError("Invalid chat_id")
        
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
    
    def notify_success(self, book_count: int, filepath: str, 
                       duration: Optional[float] = None) -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = self._build_success_message(
            book_count=book_count,
            timestamp=timestamp,
            duration=duration
        )
        
        # Enviar archivo Excel si existe
        return self._send_message_with_file(message, filepath)
    
    def notify_error(self, error_message: str, 
                     partial_results: Optional[int] = None) -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = self._build_error_message(
            error_message=error_message,
            timestamp=timestamp,
            partial_results=partial_results
        )
        
        return self._send_message_in_thread(message, parse_mode="Markdown")
    
    def _send_message_with_file(self, text: str, filepath: str) -> bool:
        """Send message with optional Excel file."""
        def send():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._send_message_with_file_async(text, filepath))
                loop.close()
            except Exception as e:
                logger.error(f"Error en thread de notificación: {e}")
        
        thread = threading.Thread(target=send, daemon=True)
        thread.start()
        thread.join(timeout=30)
        return True
    
    async def _send_message_with_file_async(self, text: str, filepath: str) -> bool:
        """Send message, optionally with Excel file."""
        try:
            # Si hay archivo, enviarlo con caption
            if filepath:
                with open(filepath, 'rb') as f:
                    await self.bot.send_document(
                        chat_id=self.chat_id,
                        document=f,
                        caption=text,
                        parse_mode="Markdown"
                    )
                logger.info(f"Excel enviado a chat {self.chat_id}")
            else:
                # Solo mensaje sin archivo
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode="Markdown"
                )
                logger.info(f"Notificación enviada a chat {self.chat_id}")
            
            return True
            
        except TelegramError as e:
            logger.error(f"Error enviando notificación: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado enviando notificación: {e}")
            return False
    
    def notify_error(self, error_message: str, 
                     partial_results: Optional[int] = None) -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        message = self._build_error_message(
            error_message=error_message,
            timestamp=timestamp,
            partial_results=partial_results
        )
        
        return self._send_message_in_thread(message, parse_mode="Markdown")
    
    def notify_started(self) -> bool:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"🕐 *Scraping iniciado*\n\n📅 {timestamp}\n\nObteniendo libros de Buscalibre Perú..."
        return self._send_message_in_thread(message, parse_mode="Markdown")
    
    def _send_message_in_thread(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message in a separate thread to avoid event loop issues."""
        def send():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._send_message_async(text, parse_mode))
                loop.close()
            except Exception as e:
                logger.error(f"Error en thread de notificación: {e}")
        
        thread = threading.Thread(target=send, daemon=True)
        thread.start()
        thread.join(timeout=10)
        return True
    
    def _build_success_message(self, book_count: int, timestamp: str,
                               duration: Optional[float]) -> str:
        duration_str = f" ({duration:.1f}s)" if duration else ""
        
        return f"""✅ *Scraping Completado* ✅

📚 *Libros extraídos hoy:* {book_count}
🕐 *Fecha:* {timestamp}
⏱️ *Duración:* {duration_str}""".strip()
    
    def _build_error_message(self, error_message: str, timestamp: str,
                             partial_results: Optional[int]) -> str:
        partial_str = f"\n📚 *Libros extraídos antes del error:* {partial_results}" if partial_results else ""
        
        return f"""❌ *Error en Scraping* ❌

🕐 *Fecha:* {timestamp}
⚠️ *Error:* {error_message}{partial_str}""".strip()
    
    async def _send_message_async(self, text: str, parse_mode: str = "Markdown") -> bool:
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            logger.info(f"Notificación enviada a chat {self.chat_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Error enviando notificación: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado enviando notificación: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.bot.get_me())
            loop.close()
            logger.info("Conexión con Telegram verificada")
            return True
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            return False