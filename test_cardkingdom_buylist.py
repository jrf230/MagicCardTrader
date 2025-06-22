#!/usr/bin/env python3
"""Test Card Kingdom buylist scraper specifically."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cardkingdom_buylist():
    """Test Card Kingdom buylist scraper."""
    print("=== Testing Card Kingdom Buylist (What They Pay) ===\n")

    scraper = CardKingdomScraper()

    # Test cards that are commonly bought by vendors
    test_cards = [
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Demonic Tutor", set_name="Revised Edition", quantity=1),
        Card(name="Lightning Bolt", set_name="Revised Edition", quantity=1),
        Card(name="Counterspell", set_name="Revised Edition", quantity=1),
        Card(name="Wrath of God", set_name="Revised Edition", quantity=1),
    ]

    for card in test_cards:
        print(f"Searching for {card.name} ({card.set_name})...")

        try:
            price_data = scraper.search_card(card)

            if price_data:
                print(f"✅ {card.name}: ${price_data.price:.2f}")
                print(
                    f"   Price Type: {price_data.all_conditions.get('price_type', 'unknown')}"
                )

                # Show additional info based on price type
                if price_data.all_conditions.get("price_type") == "buylist_confirmed":
                    buylist_prices = price_data.all_conditions.get("buylist_prices", [])
                    print(f"   Buylist Prices Found: {buylist_prices}")
                elif (
                    price_data.all_conditions.get("price_type") == "estimated_from_sell"
                ):
                    sell_prices = price_data.all_conditions.get("sell_prices", [])
                    estimated = price_data.all_conditions.get("estimated_buylist", 0)
                    print(f"   Sell Prices: {sell_prices[:5]}...")  # Show first 5
                    print(f"   Estimated Buylist: ${estimated:.2f}")

                print(
                    f"   Search URL: {price_data.all_conditions.get('search_url', 'N/A')}"
                )
            else:
                print(f"❌ {card.name}: No buylist price found")

            print()

        except Exception as e:
            print(f"❌ {card.name}: Error - {e}")
            print()

    print("=== Buylist Test Complete ===")


if __name__ == "__main__":
    test_cardkingdom_buylist()
