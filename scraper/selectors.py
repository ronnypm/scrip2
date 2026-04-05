"""
Centralized CSS selectors for Buscalibre scraper.
"""

# ============================================
# SELECTORES PRINCIPALES
# ============================================

# Contenedor de cada libro
BOOK_CONTAINER = "div.producto"
BOOK_CONTAINER_ALT = "div.box-producto"


# ============================================
# SELECTORES DE DATOS
# ============================================

# Título del libro
TITLE_SELECTOR = "h3.nombre"
TITLE_SELECTOR_ALT = "div.producto h3.nombre"

# Autor/escritor
AUTHOR_SELECTOR = "div.autor"
AUTHOR_SELECTOR_ALT = "div.producto div.autor"

# Descripción del libro (metadatos: editorial, año, formato)
DESCRIPTION_SELECTOR = "div.metas"
DESCRIPTION_SELECTOR_ALT = "div.autor.color-dark-gray"

# Precio - buscar el precio final (no el tachado)
PRICE_SELECTOR = "div.box-precios strong"
PRICE_SELECTOR_ALT = "div.producto div.box-precios strong"

# Envío rápido
FAST_SHIPPING_SELECTOR = "[data-pista='solo_despacho_24_horas']"
FAST_SHIPPING_SELECTOR_ALT = "span[data-pista*='despacho']"


# ============================================
# SELECTORES DE NAVEGACIÓN
# ============================================

# URL del libro - buscar el link dentro del contenedor
BOOK_URL_SELECTOR = "a[href^='/libro']"
BOOK_URL_SELECTOR_ALT = "div.producto a::attr(href)"


# ============================================
# HELPERS
# ============================================

def get_all_selectors() -> dict:
    return {
        "BOOK_CONTAINER": [BOOK_CONTAINER, BOOK_CONTAINER_ALT],
        "TITLE": [TITLE_SELECTOR, TITLE_SELECTOR_ALT],
        "AUTHOR": [AUTHOR_SELECTOR, AUTHOR_SELECTOR_ALT],
        "DESCRIPTION": [DESCRIPTION_SELECTOR, DESCRIPTION_SELECTOR_ALT],
        "PRICE": [PRICE_SELECTOR, PRICE_SELECTOR_ALT],
        "FAST_SHIPPING": [FAST_SHIPPING_SELECTOR, FAST_SHIPPING_SELECTOR_ALT],
    }