#!/usr/bin/env python3
"""Simple test for MTGStocks bid/offer scraper."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.mtgstocks import MTGStocksScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mtgstocks_simple():
    """Test MTGStocks bid/offer scraper with just one card."""
    print("=== Testing MTGStocks Bid/Offer Prices (Simple) ===\n")

    scraper = MTGStocksScraper()

    # Test just one card
    card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)

    print(f"Searching for {card.name} ({card.set_name})...")

    try:
        price_data = scraper.search_card(card)

        if price_data:
            print(f"✅ {card.name}: ${price_data.price:.2f}")
            print(
                f"   Price Type: {price_data.all_conditions.get('price_type', 'unknown')}"
            )

            # Show bid/offer breakdown
            bid_price = price_data.all_conditions.get("bid_price")
            offer_price = price_data.all_conditions.get("offer_price")
            market_price = price_data.all_conditions.get("market_price")
            all_prices = price_data.all_conditions.get("all_prices", {})

            if bid_price:
                print(f"   Bid (Wants): ${bid_price:.2f}")
            if offer_price:
                print(f"   Offer (Offers): ${offer_price:.2f}")
            if market_price:
                print(f"   Market: ${market_price:.2f}")
            if all_prices:
                print(f"   All Prices: {all_prices}")

            print(f"   Bid Count: {price_data.all_conditions.get('bid_count', 0)}")
            print(f"   Offer Count: {price_data.all_conditions.get('offer_count', 0)}")
            print(
                f"   Search URL: {price_data.all_conditions.get('search_url', 'N/A')}"
            )
        else:
            print(f"❌ {card.name}: No bid/offer prices found")

        print()

    except Exception as e:
        print(f"❌ {card.name}: Error - {e}")
        print()

    print("=== Simple Test Complete ===")


if __name__ == "__main__":
    test_mtgstocks_simple()
