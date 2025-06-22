"""CardShark scraper for buylist prices."""

from .base_scraper import BaseScraper
from ..models import Card, PriceData
from typing import Optional, List
from datetime import datetime


class CardSharkScraper(BaseScraper):
    """Stub: Fetches CardShark buylist prices."""

    def __init__(self):
        super().__init__("CardShark", "https://www.cardshark.com")

    def search_card(self, card: Card) -> Optional[PriceData]:
        # TODO: Implement scraping logic
        return None

    def get_buylist(self) -> List[PriceData]:
        """CardShark buylist not implemented yet, return empty list."""
        return []
