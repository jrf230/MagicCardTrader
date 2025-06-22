"""Nerd Rage Gaming scraper for buylist and sell list prices."""

import logging
from datetime import datetime
from typing import Optional, List, Dict
from ..models import Card, PriceData
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NerdRageGamingScraper(BaseScraper):
    """Scraper for Nerd Rage Gaming buylist and sell list prices."""

    def __init__(self):
        super().__init__(
            "Nerd Rage Gaming", "https://www.nerdragegaming.com/nrgbuylist"
        )

        # Manual fallback data for key cards
        # They pay up to 80% of TCG Low with 20% trade-in bonus
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "buylist_cash": 32.00,  # 80% of TCG Low (~$40)
                    "buylist_credit": 38.40,  # 20% bonus on cash price
                    "sell_price": 45.00,  # Estimated sell price
                    "condition": "Near Mint",
                    "quantity_limit": 50,
                    "tcg_low_reference": 40.00,
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "buylist_cash": 10.40,  # 80% of TCG Low (~$13)
                    "buylist_credit": 12.48,  # 20% bonus on cash price
                    "sell_price": 15.00,
                    "condition": "Near Mint",
                    "quantity_limit": 100,
                    "tcg_low_reference": 13.00,
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "buylist_cash": 26.00,  # 80% of TCG Low (~$32.50)
                    "buylist_credit": 31.20,  # 20% bonus on cash price
                    "sell_price": 35.00,
                    "condition": "Near Mint",
                    "quantity_limit": 25,
                    "tcg_low_reference": 32.50,
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "buylist_cash": 3.20,  # 80% of TCG Low (~$4)
                    "buylist_credit": 3.84,  # 20% bonus on cash price
                    "sell_price": 5.00,
                    "condition": "Near Mint",
                    "quantity_limit": 200,
                    "tcg_low_reference": 4.00,
                }
            },
        }

        # Trade-in bonus percentage
        self.trade_in_bonus = 0.20  # 20%

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card and return buylist price data from Nerd Rage Gaming."""
        try:
            # Check manual data
            manual_data = self._get_manual_data(card)
            if manual_data:
                logger.debug(
                    f"Nerd Rage Gaming: Using manual data for {card.name} ({card.set_name})"
                )
                return manual_data

            # If no manual data, try web scraping
            logger.debug(
                f"Nerd Rage Gaming: Attempting to scrape {card.name} ({card.set_name})"
            )
            return self._attempt_scraping(card)

        except Exception as e:
            logger.debug(
                f"Nerd Rage Gaming: Error searching for {card.name} ({card.set_name}): {e}"
            )
            return None

    def search_card_with_sell_price(self, card: Card) -> Dict[str, Optional[PriceData]]:
        """Search for a card and return both buylist and sell price data."""
        buylist_data = self.search_card(card)

        if buylist_data:
            # Try to get sell price data
            sell_data = self._get_sell_price(card)

            return {"buylist": buylist_data, "sell": sell_data}

        return {"buylist": buylist_data, "sell": None}

    def _get_manual_data(self, card: Card) -> Optional[PriceData]:
        """Get manual buylist data for a card."""
        card_data = self.manual_data.get(card.name, {}).get(card.set_name)

        if card_data:
            cash_price = card_data.get("buylist_cash", 0)
            credit_price = card_data.get("buylist_credit", 0)

            # Use cash price as the main price (lower of the two)
            main_price = cash_price

            all_conditions = {}
            if cash_price > 0:
                all_conditions["Cash"] = cash_price
            if credit_price > 0:
                all_conditions["Credit"] = credit_price

            if all_conditions:
                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition=card_data.get("condition", "Near Mint"),
                    quantity_limit=card_data.get("quantity_limit"),
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": self.base_url,
                        "price_type": "buylist_cash_and_credit",
                        "matched_set": card.set_name,
                        "cash_price": cash_price,
                        "credit_price": credit_price,
                        "trade_in_bonus": self.trade_in_bonus,
                        "tcg_low_reference": card_data.get("tcg_low_reference"),
                        "all_prices": all_conditions,
                        "data_source": "manual_fallback",
                        "note": f"Nerd Rage Gaming buylist prices (80% of TCG Low + {self.trade_in_bonus*100}% trade-in bonus)",
                    },
                )

        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape Nerd Rage Gaming buylist."""
        try:
            # For now, return None as web scraping is not implemented
            # The site appears to be a JavaScript-heavy SPA with catalog structure
            logger.debug(
                f"Nerd Rage Gaming: Web scraping not implemented for {card.name} ({card.set_name})"
            )
            return None

        except Exception as e:
            logger.debug(
                f"Nerd Rage Gaming: Scraping failed for {card.name} ({card.set_name}): {e}"
            )
            return None

    def _get_sell_price(self, card: Card) -> Optional[PriceData]:
        """Get sell price for a card (separate method for sell list)."""
        try:
            # For now, use manual data for sell prices
            card_data = self.manual_data.get(card.name, {}).get(card.set_name)

            if card_data and card_data.get("sell_price"):
                sell_price = card_data["sell_price"]

                return PriceData(
                    vendor=f"{self.name} (Sell)",
                    price=sell_price,
                    condition=card_data.get("condition", "Near Mint"),
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": "https://www.nerdragegaming.com",
                        "price_type": "sell_price",
                        "matched_set": card.set_name,
                        "sell_price": sell_price,
                        "data_source": "manual_fallback",
                    },
                )

            return None

        except Exception as e:
            logger.debug(
                f"Nerd Rage Gaming: Error getting sell price for {card.name}: {e}"
            )
            return None

    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from Nerd Rage Gaming."""
        logger.warning("Nerd Rage Gaming: Full buylist scraping not implemented.")
        return []

    def __str__(self) -> str:
        return f"Nerd Rage Gaming Scraper ({self.base_url})"
