"""
Parser for extracting book data from Buscalibre HTML.
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup

from . import selectors as sel


logger = logging.getLogger(__name__)


class BuscalibreParser:
    """
    Parser to extract book data from Buscalibre HTML pages.
    """
    
    def __init__(self):
        self.extraction_timestamp = datetime.now().isoformat()
    
    def parse_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse a complete HTML page and extract all books.
        
        Args:
            html: Raw HTML content of the page.
        
        Returns:
            List of book dictionaries.
        """
        soup = BeautifulSoup(html, "lxml")
        books = []
        
        # Try different container selectors
        containers = self._find_book_containers(soup)
        
        logger.info(f"Encontrados {len(containers)} libros en la página")
        
        for container in containers:
            try:
                book = self.parse_book(container)
                if book:
                    books.append(book)
            except Exception as e:
                logger.warning(f"Error parseando libro: {e}")
                continue
        
        return books
    
    def _find_book_containers(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Find all book containers using multiple selectors."""
        containers = soup.select(sel.BOOK_CONTAINER)
        
        if not containers:
            containers = soup.select(sel.BOOK_CONTAINER_ALT)
        
        return containers
    
    def parse_book(self, container: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single book container.
        
        Args:
            container: BeautifulSoup element containing book data.
        
        Returns:
            Dictionary with book data, or None if extraction fails.
        """
        try:
            title = self._extract_title(container)
            if not title:
                logger.debug("Libro sin título, saltando...")
                return None
            
            return {
                "titulo": title,
                "autor": self._extract_author(container),
                "descripcion": self._extract_description(container),
                "precio": self._extract_price(container),
                "envio_rapido": self._has_fast_shipping(container),
                "url": self._extract_url(container),
                "fecha_extraccion": self.extraction_timestamp
            }
        except Exception as e:
            logger.error(f"Error extrayendo datos del libro: {e}")
            return None
    
    def _extract_title(self, container: BeautifulSoup) -> Optional[str]:
        """Extract book title."""
        title = self._try_selectors(container, [
            sel.TITLE_SELECTOR,
            sel.TITLE_SELECTOR_ALT
        ])
        return self._clean_text(title) if title else None
    
    def _extract_author(self, container: BeautifulSoup) -> str:
        """Extract author name."""
        author = self._try_selectors(container, [
            sel.AUTHOR_SELECTOR,
            sel.AUTHOR_SELECTOR_ALT
        ])
        return self._clean_text(author) if author else "No especificado"
    
    def _extract_description(self, container: BeautifulSoup) -> str:
        """Extract book description."""
        desc = self._try_selectors(container, [
            sel.DESCRIPTION_SELECTOR,
            sel.DESCRIPTION_SELECTOR_ALT
        ])
        return self._clean_text(desc) if desc else "Sin descripción"
    
    def _extract_price(self, container: BeautifulSoup) -> Optional[float]:
        """Extract price and convert to float."""
        price = self._try_selectors(container, [
            sel.PRICE_SELECTOR,
            sel.PRICE_SELECTOR_ALT
        ])
        
        if price:
            # Clean price (remove currency symbols, etc.)
            price_clean = self._clean_price(price)
            if price_clean is not None:
                return price_clean
        
        return None
    
    def _has_fast_shipping(self, container: BeautifulSoup) -> bool:
        """Check if book has fast shipping."""
        fast_shipping = container.select(sel.FAST_SHIPPING_SELECTOR)
        
        if not fast_shipping:
            fast_shipping = container.select(sel.FAST_SHIPPING_SELECTOR_ALT)
        
        return len(fast_shipping) > 0
    
    def _extract_url(self, container: BeautifulSoup) -> str:
        """Extract book URL."""
        # Buscar directamente el link dentro del contenedor
        link = container.select_one("a[href^='/libro']")
        if link:
            url = link.get('href', '')
            if url:
                return f"https://www.buscalibre.pe{url}"
        
        # Fallback: buscar cualquier link
        link = container.select_one('a[href]')
        if link:
            url = link.get('href', '')
            if url and '/libro' in url:
                return f"https://www.buscalibre.pe{url}"
        
        return ""
    
    def _try_selectors(self, container: BeautifulSoup, 
                       selectors: List[str], attr: str = None) -> Optional[str]:
        """
        Try multiple selectors until one works.
        
        Args:
            container: BeautifulSoup element to search.
            selectors: List of CSS selectors to try.
            attr: If provided, extract this attribute instead of text.
        
        Returns:
            Text or attribute value, or None if no selector works.
        """
        for selector in selectors:
            try:
                element = container.select_one(selector)
                if element:
                    if attr:
                        return element.get(attr, "")
                    return element.get_text(strip=True)
            except Exception:
                continue
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common artifacts
        text = text.replace("\n", " ").replace("\r", "")
        
        return text.strip()
    
    def _clean_price(self, price_str: str) -> Optional[float]:
        """
        Clean price string and convert to float.
        
        Handles formats like:
        - S/ 45.90
        - S/45.90
        - 45.90
        - $45.90
        """
        if not price_str:
            return None
        
        # Remove currency symbols and whitespace
        import re
        price_str = price_str.replace("S/", "").replace("S", "").replace("$", "")
        price_str = price_str.strip()
        
        # Handle Peruvian format (comma as decimal separator): S/ 77,00 -> 77.00
        # Replace comma with dot if it's the last comma (decimal separator)
        if "," in price_str and "." not in price_str:
            # Find the last comma and check if it looks like a decimal
            parts = price_str.rsplit(",", 1)
            if len(parts) == 2 and len(parts[1]) <= 2:
                price_str = parts[0] + "." + parts[1]
        
        # Extract numeric value
        match = re.search(r"[\d.]+", price_str)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None