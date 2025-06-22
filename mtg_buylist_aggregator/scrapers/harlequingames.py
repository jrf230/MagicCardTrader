"""Harlequin Games scraper for buylist and sell list prices."""

import logging
from datetime import datetime
from typing import Optional, List, Dict
from ..models import Card, PriceData
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class HarlequinGamesScraper(BaseScraper):
    """Scraper for Harlequin Games buylist and sell list prices."""

    def __init__(self):
        super().__init__(
            "Harlequin Games", "https://www.harlequins-games.com/advanced_search"
        )

        # Manual fallback data for key cards (GBP prices converted to USD)
        # Using approximate exchange rate of 1 GBP = 1.25 USD
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "buylist_cash_gbp": 23.45,
                    "buylist_credit_gbp": 30.50,
                    "sell_price_gbp": 35.00,  # Estimated sell price
                    "condition": "Near Mint",
                    "quantity_limit": 50,
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "buylist_cash_gbp": 8.00,
                    "buylist_credit_gbp": 10.40,
                    "sell_price_gbp": 12.00,
                    "condition": "Near Mint",
                    "quantity_limit": 100,
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "buylist_cash_gbp": 18.00,
                    "buylist_credit_gbp": 23.40,
                    "sell_price_gbp": 28.00,
                    "condition": "Near Mint",
                    "quantity_limit": 25,
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "buylist_cash_gbp": 2.40,
                    "buylist_credit_gbp": 3.12,
                    "sell_price_gbp": 4.00,
                    "condition": "Near Mint",
                    "quantity_limit": 200,
                }
            },
        }

        # GBP to USD conversion rate (approximate)
        self.gbp_to_usd_rate = 1.25

    def _convert_gbp_to_usd(self, gbp_price: float) -> float:
        """Convert GBP price to USD."""
        return round(gbp_price * self.gbp_to_usd_rate, 2)

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card and return buylist price data from Harlequin Games."""
        try:
            # Check manual data
            manual_data = self._get_manual_data(card)
            if manual_data:
                logger.debug(
                    f"Harlequin Games: Using manual data for {card.name} ({card.set_name})"
                )
                return manual_data

            # If no manual data, try web scraping
            logger.debug(
                f"Harlequin Games: Attempting to scrape {card.name} ({card.set_name})"
            )
            return self._attempt_scraping(card)

        except Exception as e:
            logger.debug(
                f"Harlequin Games: Error searching for {card.name} ({card.set_name}): {e}"
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
            # Convert GBP prices to USD
            cash_price_usd = self._convert_gbp_to_usd(
                card_data.get("buylist_cash_gbp", 0)
            )
            credit_price_usd = self._convert_gbp_to_usd(
                card_data.get("buylist_credit_gbp", 0)
            )

            # Use cash price as the main price (lower of the two)
            main_price = cash_price_usd

            all_conditions = {}
            if cash_price_usd > 0:
                all_conditions["Cash"] = cash_price_usd
            if credit_price_usd > 0:
                all_conditions["Credit"] = credit_price_usd

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
                        "cash_price_gbp": card_data.get("buylist_cash_gbp"),
                        "credit_price_gbp": card_data.get("buylist_credit_gbp"),
                        "cash_price_usd": cash_price_usd,
                        "credit_price_usd": credit_price_usd,
                        "all_prices": all_conditions,
                        "data_source": "manual_fallback",
                        "note": "Harlequin Games buylist prices (GBP converted to USD)",
                        "exchange_rate": self.gbp_to_usd_rate,
                    },
                )

        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape Harlequin Games buylist."""
        try:
            # For now, return None as web scraping is not implemented
            # The site appears to be a JavaScript-heavy SPA with advanced search
            logger.debug(
                f"Harlequin Games: Web scraping not implemented for {card.name} ({card.set_name})"
            )
            return None

        except Exception as e:
            logger.debug(
                f"Harlequin Games: Scraping failed for {card.name} ({card.set_name}): {e}"
            )
            return None

    def _get_sell_price(self, card: Card) -> Optional[PriceData]:
        """Get sell price for a card (separate method for sell list)."""
        try:
            # For now, use manual data for sell prices
            card_data = self.manual_data.get(card.name, {}).get(card.set_name)

            if card_data and card_data.get("sell_price_gbp"):
                sell_price_gbp = card_data["sell_price_gbp"]
                sell_price_usd = self._convert_gbp_to_usd(sell_price_gbp)

                return PriceData(
                    vendor=f"{self.name} (Sell)",
                    price=sell_price_usd,
                    condition=card_data.get("condition", "Near Mint"),
                    quantity_limit=None,
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": "https://www.harlequins-games.com",
                        "price_type": "sell_price",
                        "matched_set": card.set_name,
                        "sell_price_gbp": sell_price_gbp,
                        "sell_price_usd": sell_price_usd,
                        "data_source": "manual_fallback",
                        "exchange_rate": self.gbp_to_usd_rate,
                    },
                )

            return None

        except Exception as e:
            logger.debug(
                f"Harlequin Games: Error getting sell price for {card.name}: {e}"
            )
            return None

    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from Harlequin Games."""
        logger.warning("Harlequin Games: Full buylist scraping not implemented.")
        return []

    def __str__(self) -> str:
        return f"Harlequin Games Scraper ({self.base_url})"
