"""
Main entry point for Buscalibre scraper.

Usage:
    python main.py                    # Run once
    python main.py --schedule        # Run on schedule
    python main.py --test-notify    # Test Telegram notification
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_config, load_required_env_vars, get_config_path
from scraper.spider import BuscalibreSpider, ScraperError
from export.excel import ExcelExporter
from notifier.telegram import TelegramNotifier
from notifier.email import EmailNotifier
import schedule


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


def run_scraper(config: dict) -> bool:
    """
    Run the scraper with given configuration.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        True if successful, False otherwise.
    """
    logger.info("=" * 50)
    logger.info("Iniciando scraper de Buscalibre Perú")
    logger.info("=" * 50)
    
    # Initialize notifier
    try:
        notifier = TelegramNotifier(
            bot_token=config["telegram"]["bot_token"],
            chat_id=config["telegram"]["chat_id"]
        )
        
        # Test connection
        if not notifier.test_connection():
            logger.error("No se pudo conectar con Telegram")
            return False
        
        # Notify started
        notifier.notify_started()
        
    except Exception as e:
        logger.warning(f"No se pudo inicializar notificador: {e}")
        notifier = None
    
    # Initialize email notifier
    email_notifier = None
    if "gmail" in config and config["gmail"].get("email"):
        try:
            email_notifier = EmailNotifier(
                email=config["gmail"]["email"],
                app_password=config["gmail"]["app_password"],
                to_emails=config["gmail"]["to"]
            )
            logger.info("Email notifier inicializado")
        except Exception as e:
            logger.warning(f"No se pudo inicializar email notifier: {e}")
    
    start_time = time.time()
    books = []
    error_message = None
    
    try:
        # Create and run spider
        spider = BuscalibreSpider(config["scraper"])
        books = spider.run()
        
        stats = spider.get_stats()
        logger.info(f"Estadísticas: {stats}")
        
    except ScraperError as e:
        error_message = str(e)
        logger.error(f"Error en scraper: {e}")
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error inesperado: {e}")
    
    # Export to Excel
    filepath = None
    try:
        exporter = ExcelExporter()
        filepath = exporter.export(books, config["output"]["directory"])
        logger.info(f"Excel generado: {filepath}")
        
    except Exception as e:
        logger.error(f"Error exportando a Excel: {e}")
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Send notification
    if notifier:
        if error_message:
            notifier.notify_error(
                error_message=error_message,
                partial_results=len(books) if books else None
            )
        else:
            notifier.notify_success(
                book_count=len(books),
                filepath=filepath or "",
                duration=duration
            )
    
    # Send email with Excel if configured
    if email_notifier and filepath and not error_message:
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"Libros Buscalibre - {today}"
            body = f"Se extrajeron {len(books)} libros de envío rápido.\n\nAdjunto el Excel con todos los detalles."
            email_notifier.send_excel(filepath, subject=subject, body=body)
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    logger.info(f"Scraping completado en {duration:.2f}s")
    logger.info(f"Total de libros: {len(books)}")
    
    return error_message is None


def run_scheduled(config: dict):
    """Run scraper on a schedule."""
    hour = config["scheduler"].get("hour", 9)
    minute = config["scheduler"].get("minute", 0)
    
    logger.info(f"Programado para ejecutar a las {hour:02d}:{minute:02d}")
    
    # Run immediately first
    run_scraper(config)
    
    # Schedule for future runs
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_scraper, config=config)
    
    logger.info("Esperando próximas ejecuciones...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


def test_notification(config: dict) -> bool:
    """Test Telegram notification."""
    try:
        notifier = TelegramNotifier(
            bot_token=config["telegram"]["bot_token"],
            chat_id=config["telegram"]["chat_id"]
        )
        
        if notifier.test_connection():
            print("✅ Conexión con Telegram exitosa!")
            
            # Send test message
            notifier.notify_success(
                book_count=0,
                filepath="test.xlsx",
                duration=0.1
            )
            print("✅ Notificación de prueba enviada!")
            return True
        else:
            print("❌ No se pudo conectar con Telegram")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scraper para Buscalibre Perú"
    )
    
    parser.add_argument(
        "--schedule", 
        action="store_true",
        help="Ejecutar en modo programado (daily)"
    )
    
    parser.add_argument(
        "--test-notify",
        action="store_true",
        help="Probar conexión con Telegram"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Ruta al archivo de configuración"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        if args.config:
            config = load_config(Path(args.config))
        else:
            config = load_config()
        
        # Check required values
        load_required_env_vars(config)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nCopia config.yaml.example a config.yaml y complétalo.")
        sys.exit(1)
        
    except ValueError as e:
        print(f"Error de configuración: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        sys.exit(1)
    
    # Run appropriate mode
    if args.test_notify:
        success = test_notification(config)
        sys.exit(0 if success else 1)
        
    elif args.schedule:
        if not config["scheduler"]["enabled"]:
            print("Advertencia: scheduler.enabled=false en config")
        run_scheduled(config)
        
    else:
        success = run_scraper(config)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()