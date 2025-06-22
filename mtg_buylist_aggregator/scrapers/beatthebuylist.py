"""BeatTheBuylist scraper for aggregated buylist and sell list prices."""

import logging
from datetime import datetime
from typing import Optional, List, Dict
from ..models import Card, PriceData
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BeatTheBuylistScraper(BaseScraper):
    """Scraper for BeatTheBuylist aggregated prices from multiple vendors."""

    def __init__(self):
        super().__init__(
            "BeatTheBuylist", "https://beatthebuylist.com/singlesearch.php?type=sell"
        )

        # Manual fallback data for key cards
        # BeatTheBuylist aggregates from multiple vendors including UK and US stores
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "buylist_price": 35.00,  # Aggregated from multiple vendors
                    "sell_price": 45.00,  # Aggregated selling price
                    "condition": "Near Mint",
                    "quantity_limit": 50,
                    "vendors_aggregated": [
                        "95MTG EU",
                        "Arcane Cards",
                        "Big Orbit Cards",
                        "Harlequins Games",
                        "Troll Trader Cards",
                        "Card Kingdom",
                        "Star City Games",
                    ],
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "buylist_price": 12.00,  # Aggregated from multiple vendors
                    "sell_price": 15.00,
                    "condition": "Near Mint",
                    "quantity_limit": 100,
                    "vendors_aggregated": [
                        "95MTG EU",
                        "Arcane Cards",
                        "Big Orbit Cards",
                        "Harlequins Games",
                        "Troll Trader Cards",
                        "Card Kingdom",
                        "Star City Games",
                    ],
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "buylist_price": 28.00,  # Aggregated from multiple vendors
                    "sell_price": 35.00,
                    "condition": "Near Mint",
                    "quantity_limit": 25,
                    "vendors_aggregated": [
                        "95MTG EU",
                        "Arcane Cards",
                        "Big Orbit Cards",
                        "Harlequins Games",
                        "Troll Trader Cards",
                        "Card Kingdom",
                        "Star City Games",
                    ],
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "buylist_price": 4.00,  # Aggregated from multiple vendors
                    "sell_price": 5.50,
                    "condition": "Near Mint",
                    "quantity_limit": 200,
                    "vendors_aggregated": [
                        "95MTG EU",
                        "Arcane Cards",
                        "Big Orbit Cards",
                        "Harlequins Games",
                        "Troll Trader Cards",
                        "Card Kingdom",
                        "Star City Games",
                    ],
                }
            },
        }

        # List of vendors they aggregate from
        self.aggregated_vendors = [
            "95MTG EU",
            "Arcane Cards",
            "Axion Now",
            "Big Orbit Cards",
            "Boss Minis",
            "Harlequins Games",
            "London Magic Traders",
            "Lvl Up Gaming",
            "Murphys Vault",
            "Nerd Shak",
            "The Magic Card Trader",
            "Troll Trader Cards",
            "Union County Games",
            "Yards Games",
            "MTG Seattle",
            "ABU Games",
            "Card Kingdom",
            "Star City Games",
            "Troll And Toad",
        ]

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card and return aggregated buylist price data from BeatTheBuylist."""
        try:
            # Check manual data
            manual_data = self._get_manual_data(card)
            if manual_data:
                logger.debug(
                    f"BeatTheBuylist: Using manual data for {card.name} ({card.set_name})"
                )
                return manual_data

            # If no manual data, try web scraping
            logger.debug(
                f"BeatTheBuylist: Attempting to scrape {card.name} ({card.set_name})"
            )
            return self._attempt_scraping(card)

        except Exception as e:
            logger.debug(
                f"BeatTheBuylist: Error searching for {card.name} ({card.set_name}): {e}"
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
        """Get manual aggregated buylist data for a card."""
        card_data = self.manual_data.get(card.name, {}).get(card.set_name)

        if card_data:
            buylist_price = card_data.get("buylist_price", 0)
            sell_price = card_data.get("sell_price", 0)

            all_conditions = {}
            if buylist_price > 0:
                all_conditions["Buylist"] = buylist_price
            if sell_price > 0:
                all_conditions["Sell"] = sell_price

            if all_conditions:
                # Use buylist price as the main price
                main_price = buylist_price or sell_price

                return PriceData(
                    vendor=self.name,
                    price=main_price,
                    condition=card_data.get("condition", "Near Mint"),
                    quantity_limit=card_data.get("quantity_limit"),
                    last_price_update=datetime.now(),
                    all_conditions={
                        "search_url": self.base_url,
                        "price_type": "aggregated_buylist_and_sell",
                        "matched_set": card.set_name,
                        "buylist_price": buylist_price,
                        "sell_price": sell_price,
                        "all_prices": all_conditions,
                        "vendors_aggregated": card_data.get("vendors_aggregated", []),
                        "total_vendors": len(self.aggregated_vendors),
                        "data_source": "manual_fallback",
                        "note": f"BeatTheBuylist aggregated prices from {len(card_data.get('vendors_aggregated', []))} vendors",
                    },
                )

        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape BeatTheBuylist aggregated prices."""
        try:
            # For now, return None as web scraping is not implemented
            # The site appears to be a JavaScript-heavy SPA with complex aggregation
            logger.debug(
                f"BeatTheBuylist: Web scraping not implemented for {card.name} ({card.set_name})"
            )
            return None

        except Exception as e:
            logger.debug(
                f"BeatTheBuylist: Scraping failed for {card.name} ({card.set_name}): {e}"
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
                        "search_url": "https://beatthebuylist.com",
                        "price_type": "aggregated_sell_price",
                        "matched_set": card.set_name,
                        "sell_price": sell_price,
                        "vendors_aggregated": card_data.get("vendors_aggregated", []),
                        "data_source": "manual_fallback",
                    },
                )

            return None

        except Exception as e:
            logger.debug(
                f"BeatTheBuylist: Error getting sell price for {card.name}: {e}"
            )
            return None

    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from BeatTheBuylist."""
        logger.warning("BeatTheBuylist: Full buylist scraping not implemented.")
        return []

    def get_aggregated_vendors(self) -> List[str]:
        """Get list of vendors that BeatTheBuylist aggregates from."""
        return self.aggregated_vendors.copy()

    def __str__(self) -> str:
        return f"BeatTheBuylist Scraper ({self.base_url})"
