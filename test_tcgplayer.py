#!/usr/bin/env python3
"""Test TCG Player scraper."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.tcgplayer import TCGPlayerScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tcgplayer():
    """Test TCG Player scraper."""
    print("=== Testing TCG Player Scraper ===\n")

    scraper = TCGPlayerScraper()

    # Test cards
    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Lightning Bolt", set_name="Revised Edition", quantity=1),
    ]

    for card in test_cards:
        print(f"Searching for {card.name} ({card.set_name})...")

        try:
            price_data = scraper.search_card(card)

            if price_data:
                print(f"✅ {card.name}: ${price_data.price:.2f}")
                print(f"   Vendor: {price_data.vendor}")
                print(f"   Condition: {price_data.condition}")
                print(
                    f"   Search Query: {price_data.all_conditions.get('search_query', 'N/A')}"
                )
                print(f"   URL: {price_data.all_conditions.get('url', 'N/A')}")
            else:
                print(f"❌ {card.name}: No price found")

            print()

        except Exception as e:
            print(f"❌ {card.name}: Error - {e}")
            print()

    print("=== TCG Player Test Complete ===")


if __name__ == "__main__":
    test_tcgplayer()
