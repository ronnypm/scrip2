"""
Spider for scraping Buscalibre website using Playwright.
"""
import logging
import time
from typing import List, Dict, Any
from datetime import datetime

from playwright.sync_api import sync_playwright

from .parser import BuscalibreParser


logger = logging.getLogger(__name__)


class BuscalibreSpider:
    """Spider to scrape books from Buscalibre Perú using Playwright."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "")
        self.pages = config.get("pages", 5)
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)
        
        self.parser = BuscalibreParser()
        self.browser = None
        self.context = None
        self.page = None
        
        self.stats = {
            "pages_scraped": 0,
            "pages_failed": 0,
            "books_extracted": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _init_browser(self):
        """Initialize Playwright browser."""
        if self.browser is not None:
            return
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout * 1000)
        
        logger.info("Browser Playwright inicializado")
    
    def run(self) -> List[Dict[str, Any]]:
        """Run the spider to scrape all pages."""
        logger.info(f"Iniciando scraping de {self.pages} páginas")
        self.stats["start_time"] = datetime.now()
        
        try:
            self._init_browser()
        except Exception as e:
            logger.error(f"Error inicializando browser: {e}")
            self.stats["end_time"] = datetime.now()
            return []
        
        all_books = []
        
        for page_num in range(1, self.pages + 1):
            logger.info(f"Scraping página {page_num}/{self.pages}")
            
            try:
                books = self.scrape_page(page_num)
                all_books.extend(books)
                
                self.stats["pages_scraped"] += 1
                self.stats["books_extracted"] += len(books)
                
                logger.info(f"  → {len(books)} libros extraídos")
                
                if page_num < self.pages:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error en página {page_num}: {e}")
                self.stats["pages_failed"] += 1
                continue
        
        self.stats["end_time"] = datetime.now()
        
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        logger.info(f"Scraping completado en {duration:.2f}s")
        logger.info(f"Total: {len(all_books)} libros de {self.stats['pages_scraped']} páginas")
        
        return all_books
    
    def scrape_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Scrape a single page."""
        url = self._build_page_url(page_num)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"  Intento {attempt}/{self.max_retries}: {url}")
                
                self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                
                # Wait for content to load
                time.sleep(3)
                
                # Scroll to trigger lazy loading
                for _ in range(3):
                    self.page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(1)
                
                # Get page source and parse
                html = self.page.content()
                books = self.parser.parse_page(html)
                
                return books
                
            except Exception as e:
                logger.warning(f"  Intento {attempt} falló: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(attempt * 2)
                else:
                    raise
        
        return []
    
    def _build_page_url(self, page_num: int) -> str:
        """Build the URL for a specific page."""
        if page_num == 1:
            return self.base_url
        
        if "?" in self.base_url:
            return f"{self.base_url}&page={page_num}"
        else:
            return f"{self.base_url}?page={page_num}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        stats = self.stats.copy()
        
        if stats["start_time"] and stats["end_time"]:
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["duration_seconds"] = duration
        
        return stats
    
    def close(self):
        """Close the browser."""
        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
        except Exception:
            pass
        
        self.browser = None
        self.page = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


class ScraperError(Exception):
    """Custom exception for scraper errors."""
    pass