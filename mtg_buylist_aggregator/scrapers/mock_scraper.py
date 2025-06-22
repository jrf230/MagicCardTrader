"""Mock scraper for testing and demonstration purposes."""

import logging
import random
from typing import Optional, List

from .base_scraper import BaseScraper
from ..models import Card, PriceData

logger = logging.getLogger(__name__)


class MockScraper(BaseScraper):
    """Mock scraper that returns realistic test data."""

    def __init__(self, name: str = "Mock Vendor"):
        """Initialize the mock scraper."""
        super().__init__(name, "https://mock-vendor.com")
        self.price_multipliers = {
            "Star City Games": 0.8,
            "Card Kingdom": 0.75,
            "BeatTheBuylist": 0.85,
        }

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Return mock price data for testing."""
        try:
            # Generate realistic mock prices based on card characteristics
            base_price = self._get_base_price(card)
            if base_price == 0:
                return None

            # Apply vendor-specific multiplier
            multiplier = self.price_multipliers.get(self.name, 0.8)
            price = base_price * multiplier

            # Add some randomness
            price *= random.uniform(0.9, 1.1)
            price = round(price, 2)

            # Determine condition
            condition = random.choice(["NM", "LP", "MP"])

            # Quantity limit
            quantity_limit = random.choice([None, 10, 20, 50, 100])

            logger.info(
                f"Mock {self.name}: Generated price for {card.name}: ${price} ({condition})"
            )

            return PriceData(
                vendor=self.name,
                price=price,
                condition=condition,
                quantity_limit=quantity_limit,
                last_price_update=None,
            )

        except Exception as e:
            logger.error(
                f"Mock {self.name}: Error generating price for {card.name}: {e}"
            )
            return None

    def _get_base_price(self, card: Card) -> float:
        """Get base price for a card based on its characteristics."""
        # Popular cards with known approximate values
        popular_cards = {
            "Sol Ring": 5.0,
            "Rhystic Study": 25.0,
            "Demonic Tutor": 15.0,
            "Counterspell": 1.0,
            "Lightning Bolt": 2.0,
            "Wrath of God": 3.0,
            "Path to Exile": 4.0,
            "Thoughtseize": 12.0,
            "Snapcaster Mage": 35.0,
            "Tarmogoyf": 45.0,
        }

        base_price = popular_cards.get(card.name, 0)

        # Adjust for foil
        if card.is_foil():
            base_price *= 2.5

        # Adjust for condition
        if card.condition.value == "Lightly Played":
            base_price *= 0.8
        elif card.condition.value == "Moderately Played":
            base_price *= 0.6
        elif card.condition.value == "Heavily Played":
            base_price *= 0.4

        return base_price

    def get_buylist(self) -> List[PriceData]:
        """Get mock buylist data."""
        logger.warning(f"Mock {self.name}: Full buylist not implemented.")
        return []

    def __str__(self) -> str:
        return f"Mock Scraper ({self.name})"
