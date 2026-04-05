"""
Flask server for Railway deployment.
Provides /scrape endpoint to trigger the scraper.
"""
import os
import sys
import logging
from pathlib import Path

from flask import Flask, jsonify

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_config
from scraper.spider import BuscalibreSpider
from export.excel import ExcelExporter
from notifier.telegram import TelegramNotifier
from notifier.email import EmailNotifier


app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.route("/")
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "service": "Buscalibre Scraper",
        "endpoints": {
            "/": "Health check",
            "/scrape": "Trigger scraping"
        }
    })


@app.route("/scrape")
def scrape():
    """Trigger the scraper and send notifications."""
    try:
        logger.info("Iniciando scraping desde endpoint /scrape")
        
        # Load config
        config = load_config()
        
        # Initialize notifiers
        telegram_notifier = None
        email_notifier = None
        
        try:
            telegram_notifier = TelegramNotifier(
                bot_token=config["telegram"]["bot_token"],
                chat_id=config["telegram"]["chat_id"]
            )
            telegram_notifier.notify_started()
        except Exception as e:
            logger.warning(f"No se pudo inicializar Telegram: {e}")
        
        if "gmail" in config and config["gmail"].get("email"):
            try:
                email_notifier = EmailNotifier(
                    email=config["gmail"]["email"],
                    app_password=config["gmail"]["app_password"],
                    to_emails=config["gmail"]["to"]
                )
            except Exception as e:
                logger.warning(f"No se pudo inicializar email: {e}")
        
        # Run scraper
        spider = BuscalibreSpider(config["scraper"])
        books = spider.run()
        
        # Export to Excel
        filepath = None
        try:
            exporter = ExcelExporter()
            filepath = exporter.export(books, config["output"]["directory"])
            logger.info(f"Excel generado: {filepath}")
        except Exception as e:
            logger.error(f"Error exportando: {e}")
        
        # Send notifications
        if telegram_notifier:
            try:
                telegram_notifier.notify_success(
                    book_count=len(books),
                    filepath=filepath or "",
                    duration=None
                )
            except Exception as e:
                logger.error(f"Error enviando notificación Telegram: {e}")
        
        if email_notifier and filepath:
            try:
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                email_notifier.send_excel(
                    filepath,
                    subject=f"Libros Buscalibre - {today}",
                    body=f"Se extrajeron {len(books)} libros de envío rápido."
                )
            except Exception as e:
                logger.error(f"Error enviando email: {e}")
        
        return jsonify({
            "status": "success",
            "books_extracted": len(books),
            "excel_file": os.path.basename(filepath) if filepath else None
        })
        
    except Exception as e:
        logger.error(f"Error en scrape: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)