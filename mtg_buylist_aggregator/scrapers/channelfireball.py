"""Channel Fireball buylist scraper for MTG cards."""

import logging
import requests
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import re

from .base_scraper import BaseScraper
from ..models import Card, PriceData

logger = logging.getLogger(__name__)


class ChannelFireballScraper(BaseScraper):
    """Scrapes Channel Fireball for buylist prices."""

    def __init__(self):
        super().__init__("Channel Fireball", "https://store.channelfireball.com")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        self.base_url = "https://store.channelfireball.com"

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for buylist price of a card on Channel Fireball."""
        try:
            # Build search query
            query = self._build_search_query(card)

            # Search for the card
            search_url = f"{self.base_url}/search"
            params = {"q": query, "type": "product"}

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            # Extract buylist price from search results
            buylist_price = self._extract_buylist_price(response.text, card)

            if buylist_price:
                return PriceData(
                    vendor="Channel Fireball",
                    price=buylist_price,
                    condition="Near Mint",
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "buylist_price": buylist_price,
                        "condition": "Near Mint",
                    },
                )

            return None

        except Exception as e:
            logger.error(f"Error searching Channel Fireball for {card.name}: {e}")
            return None

    def get_buylist(self) -> List[PriceData]:
        """Channel Fireball buylist not implemented yet, return empty list."""
        return []

    def _build_search_query(self, card: Card) -> str:
        """Build Channel Fireball search query for a card."""
        query_parts = [card.name]

        # Add set information
        if card.set_name:
            query_parts.append(card.set_name)

        # Add foil information
        if card.is_foil():
            query_parts.append("Foil")

        return " ".join(query_parts)

    def _extract_buylist_price(self, html: str, card: Card) -> Optional[float]:
        """Extract buylist price from HTML content."""
        try:
            # Look for buylist price patterns in the HTML
            # This is a simplified approach - would need refinement based on actual site structure
            price_patterns = [
                r"buylist.*?\$([\d,]+\.?\d*)",
                r"buy.*?price.*?\$([\d,]+\.?\d*)",
                r"cash.*?price.*?\$([\d,]+\.?\d*)",
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    return float(matches[0].replace(",", ""))

            return None

        except Exception as e:
            logger.error(f"Error extracting buylist price: {e}")
            return None
