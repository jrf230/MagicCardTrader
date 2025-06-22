#!/usr/bin/env python3
"""Test cash and credit prices from vendors."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.scrapers.starcitygames import StarCityGamesScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cash_credit_prices():
    """Test cash and credit prices from vendors."""
    print("=== Testing Cash and Credit Prices ===\n")

    # Initialize scrapers
    scrapers = {
        "Card Kingdom": CardKingdomScraper(),
        "Star City Games": StarCityGamesScraper(),
    }

    # Test card
    test_card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)

    print(f"Testing card: {test_card.name} ({test_card.set_name})\n")

    for vendor_name, scraper in scrapers.items():
        print(f"--- {vendor_name} ---")

        try:
            # Get both cash and credit prices
            if hasattr(scraper, "search_card_with_credit"):
                price_data = scraper.search_card_with_credit(test_card)
                cash_data = price_data.get("cash")
                credit_data = price_data.get("credit")
            else:
                # Fallback to regular search
                cash_data = scraper.search_card(test_card)
                credit_data = None

            if cash_data:
                print(f"✅ {vendor_name}: ${cash_data.price:.2f}")
                print(f"   Condition: {cash_data.condition}")
                print(
                    f"   Data Source: {cash_data.all_conditions.get('data_source', 'scraped')}"
                )

                # Show credit price if available
                if credit_data:
                    print(f"✅ {vendor_name} (Credit): ${credit_data.price:.2f}")
                    print(f"   Condition: {credit_data.condition}")
                    print(
                        f"   Credit Multiplier: {credit_data.all_conditions.get('credit_multiplier', 'N/A')}"
                    )
                elif cash_data.all_conditions.get("credit_price"):
                    credit_price = cash_data.all_conditions["credit_price"]
                    print(f"✅ {vendor_name} (Credit): ${credit_price:.2f}")
                    print(
                        f"   Credit Multiplier: {cash_data.all_conditions.get('credit_multiplier', 'N/A')}"
                    )
                else:
                    print(f"❌ {vendor_name} (Credit): No credit price available")

            else:
                print(f"❌ {vendor_name}: No price data found")
                print(f"❌ {vendor_name} (Credit): No price data found")

            print()

        except Exception as e:
            print(f"❌ {vendor_name}: Error - {e}")
            print()

    print("=== Cash/Credit Test Complete ===")


if __name__ == "__main__":
    test_cash_credit_prices()
