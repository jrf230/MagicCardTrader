"""Card Conduit scraper for consignment/bulk pricing."""

from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime


class CardConduitScraper(BaseScraper):
    """Stub: Fetches Card Conduit consignment/bulk pricing."""

    def __init__(self):
        super().__init__("Card Conduit", "https://www.cardconduit.com")

    def search_card(self, card: Card) -> Optional[PriceData]:
        # TODO: Implement scraping logic
        return None

    def get_buylist(self) -> List[PriceData]:
        """Card Conduit buylist not implemented yet, return empty list."""
        return []
