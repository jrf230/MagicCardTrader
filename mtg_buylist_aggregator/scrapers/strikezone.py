"""StrikeZoneOnline scraper for buylist prices."""

import logging
from datetime import datetime
from typing import Optional, List
from ..models import Card, PriceData
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class StrikeZoneScraper(BaseScraper):
    """Scraper for StrikeZoneOnline buylist prices."""

    def __init__(self):
        super().__init__(
            "StrikeZoneOnline",
            "http://shop.strikezoneonline.com/BuyList/Magic_the_Gathering_Singles.html",
        )
        # Manual fallback data for key cards
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": [
                    {
                        "condition": "Near Mint Foil",
                        "language": "English",
                        "quantity": 3,
                        "price": 200.00,
                    },
                    {
                        "condition": "Near Mint Normal",
                        "language": "English",
                        "quantity": 12,
                        "price": 36.00,
                    },
                    {
                        "condition": "Light Play Normal",
                        "language": "English",
                        "quantity": 2,
                        "price": 32.00,
                    },
                ]
            }
        }

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Return buylist price data for a card from manual fallback."""
        card_data = self.manual_data.get(card.name, {}).get(card.set_name)
        if card_data:
            # Return the best (highest) price for the best condition
            best = max(card_data, key=lambda x: x["price"])
            return PriceData(
                vendor=self.name,
                price=best["price"],
                condition=best["condition"],
                quantity_limit=best["quantity"],
                last_price_update=datetime.now(),
                all_conditions={
                    "search_url": self.base_url,
                    "matched_set": card.set_name,
                    "manual_rows": card_data,
                    "data_source": "manual_fallback",
                    "note": "StrikeZoneOnline buylist prices (manual)",
                },
            )
        return None

    def get_buylist(self) -> List[PriceData]:
        logger.warning("StrikeZoneOnline: Full buylist scraping not implemented.")
        return []

    def __str__(self):
        return f"StrikeZoneOnline Scraper ({self.base_url})"
