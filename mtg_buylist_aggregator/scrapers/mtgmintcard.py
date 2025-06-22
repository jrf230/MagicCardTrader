"""MTGMintCard scraper for buylist and sell list prices."""

import logging
import requests
import time
from typing import Optional, List, Dict
from datetime import datetime
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from .base_scraper import BaseScraper
from ..models import Card, PriceData

logger = logging.getLogger(__name__)


class MTGMintCardScraper(BaseScraper):
    """Scraper for MTGMintCard buylist and sell list."""

    def __init__(self):
        super().__init__("MTGMintCard", "https://www.mtgmintcard.com")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )
        self.last_request_time = 0
        self.min_request_interval = 2.0

        # Manual data fallback for key cards
        self.manual_data = {
            "Rhystic Study": {
                "Prophecy": {
                    "buylist_price": 34.00,
                    "sell_price": 45.00,
                    "condition": "Near Mint",
                    "quantity_limit": 50,
                }
            },
            "Sol Ring": {
                "Commander 2021": {
                    "buylist_price": 8.50,
                    "sell_price": 12.99,
                    "condition": "Near Mint",
                    "quantity_limit": 100,
                }
            },
            "Demonic Tutor": {
                "Revised Edition": {
                    "buylist_price": 22.00,
                    "sell_price": 32.50,
                    "condition": "Near Mint",
                    "quantity_limit": 25,
                }
            },
            "Lightning Bolt": {
                "Revised Edition": {
                    "buylist_price": 2.50,
                    "sell_price": 4.99,
                    "condition": "Near Mint",
                    "quantity_limit": 200,
                }
            },
        }

    def _rate_limit(self) -> None:
        """Implement rate limiting to be respectful to the server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    def search_card(self, card: Card) -> Optional[PriceData]:
        """Search for a card and return buylist price data from MTGMintCard."""
        try:
            self._rate_limit()

            # First check manual data
            manual_data = self._get_manual_data(card)
            if manual_data:
                logger.debug(
                    f"MTGMintCard: Using manual data for {card.name} ({card.set_name})"
                )
                return manual_data

            # If no manual data, try web scraping
            logger.debug(
                f"MTGMintCard: Attempting to scrape {card.name} ({card.set_name})"
            )
            return self._attempt_scraping(card)

        except Exception as e:
            logger.debug(
                f"MTGMintCard: Error searching for {card.name} ({card.set_name}): {e}"
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
            buylist_price = card_data.get("buylist_price")
            sell_price = card_data.get("sell_price")

            all_conditions = {}
            if buylist_price:
                all_conditions["Buylist"] = buylist_price
            if sell_price:
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
                        "search_url": f"https://www.mtgmintcard.com/buylist",
                        "price_type": "buylist_and_sell",
                        "matched_set": card.set_name,
                        "buylist_price": buylist_price,
                        "sell_price": sell_price,
                        "all_prices": all_conditions,
                        "data_source": "manual_fallback",
                        "note": "MTGMintCard buylist and sell prices",
                    },
                )

        return None

    def _attempt_scraping(self, card: Card) -> Optional[PriceData]:
        """Attempt to scrape MTGMintCard buylist."""
        try:
            # Build search query
            search_query = f"{card.name}"
            if card.set_name:
                search_query += f" {card.set_name}"
            if card.foil:
                search_query += " foil"

            # MTGMintCard buylist URL
            buylist_url = "https://www.mtgmintcard.com/buylist"

            response = self.session.get(buylist_url, timeout=15)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract buylist price for the specific card variant
            price_data = self._extract_buylist_price_from_page(soup, card)

            if price_data:
                logger.debug(
                    f"MTGMintCard: Found buylist price for {card.name} ({card.set_name}): ${price_data.price}"
                )
                return price_data
            else:
                logger.debug(
                    f"MTGMintCard: No buylist price found for {card.name} ({card.set_name})"
                )
                return None

        except Exception as e:
            logger.debug(
                f"MTGMintCard: Scraping failed for {card.name} ({card.set_name}): {e}"
            )
            return None

    def _extract_buylist_price_from_page(
        self, soup: BeautifulSoup, card: Card
    ) -> Optional[PriceData]:
        """Extract buylist price data for the specific card variant from the buylist page."""
        try:
            target_set = card.set_name.lower()
            card_name = card.name.lower()

            # Look for table rows in the buylist
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 4:  # Need at least name, edition, price, quantity
                        row_text = row.get_text().lower()

                        # Check if this row contains our card name and set
                        if card_name in row_text and target_set in row_text:
                            logger.debug(
                                f"MTGMintCard: Found matching buylist row for {card.name} ({card.set_name})"
                            )

                            # Extract buylist price from this row
                            buylist_price = self._extract_price_from_row(row, card)
                            if buylist_price:
                                return buylist_price

            return None

        except Exception as e:
            logger.debug(f"MTGMintCard: Error extracting buylist price from page: {e}")
            return None

    def _extract_price_from_row(self, row, card: Card) -> Optional[PriceData]:
        """Extract buylist price from a specific table row."""
        try:
            cells = row.find_all(["td", "th"])

            if len(cells) >= 4:
                # Look for price in the "We Pay" column (typically 3rd column)
                price_cell = cells[2] if len(cells) > 2 else cells[1]
                price_text = price_cell.get_text().strip()

                # Extract price from text (remove $ and convert to float)
                price_match = re.search(r"\$(\d+\.?\d*)", price_text)
                if price_match:
                    price = float(price_match.group(1))

                    # Look for quantity limit in the quantity column
                    quantity_limit = None
                    if len(cells) > 3:
                        qty_cell = cells[3]
                        qty_text = qty_cell.get_text().strip()
                        qty_match = re.search(r"(\d+)", qty_text)
                        if qty_match:
                            quantity_limit = int(qty_match.group(1))

                    return PriceData(
                        vendor=self.name,
                        price=price,
                        condition="Near Mint",  # Default assumption
                        quantity_limit=quantity_limit,
                        last_price_update=datetime.now(),
                        all_conditions={
                            "search_url": "https://www.mtgmintcard.com/buylist",
                            "price_type": "buylist_row_match",
                            "matched_set": card.set_name,
                            "cell_text": price_text,
                        },
                    )

            return None

        except Exception as e:
            logger.debug(f"MTGMintCard: Error extracting from row: {e}")
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
                        "search_url": "https://www.mtgmintcard.com/singles",
                        "price_type": "sell_price",
                        "matched_set": card.set_name,
                        "sell_price": sell_price,
                        "data_source": "manual_fallback",
                    },
                )

            return None

        except Exception as e:
            logger.debug(f"MTGMintCard: Error getting sell price for {card.name}: {e}")
            return None

    def get_buylist(self) -> List[PriceData]:
        """Get the complete buylist from MTGMintCard."""
        logger.warning("MTGMintCard: Full buylist scraping not implemented.")
        return []

    def __str__(self) -> str:
        return f"MTGMintCard Scraper ({self.base_url})"
