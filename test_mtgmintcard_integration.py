#!/usr/bin/env python3
"""Test MTGMintCard integration with scraper manager."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.scraper_manager import ScraperManager
from mtg_buylist_aggregator.models import Card


def test_mtgmintcard_integration():
    """Test MTGMintCard integration with the scraper manager."""

    print("Testing MTGMintCard Integration with Scraper Manager")
    print("=" * 60)

    # Initialize scraper manager with real data
    manager = ScraperManager(use_mock=False)

    print(f"Available vendors: {manager.get_available_vendors()}")
    print()

    # Test with Rhystic Study (Prophecy)
    test_card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)

    print(f"Testing card: {test_card.name} ({test_card.set_name})")
    print("-" * 50)

    try:
        # Get prices from all vendors
        card_prices = manager.get_card_prices(test_card)

        print(f"Found prices from {len(card_prices.prices)} vendors:")
        print()

        for vendor, price_data in card_prices.prices.items():
            print(f"  {vendor}:")
            print(f"    Price: ${price_data.price}")
            print(f"    Condition: {price_data.condition}")
            print(f"    Vendor: {price_data.vendor}")

            # Check for MTGMintCard specific data
            if "MTGMintCard" in vendor:
                if price_data.all_conditions.get("buylist_price"):
                    print(f"    Buylist: ${price_data.all_conditions['buylist_price']}")
                if price_data.all_conditions.get("sell_price"):
                    print(f"    Sell: ${price_data.all_conditions['sell_price']}")
                if price_data.all_conditions.get("data_source"):
                    print(
                        f"    Data Source: {price_data.all_conditions['data_source']}"
                    )
            print()

        # Show best price
        if card_prices.best_price:
            print(
                f"Best price: ${card_prices.best_price} from {card_prices.best_vendor}"
            )
        else:
            print("No prices found")

    except Exception as e:
        print(f"Error: {e}")


def test_mtgmintcard_vs_other_vendors():
    """Compare MTGMintCard prices with other vendors."""

    print("\nComparing MTGMintCard with Other Vendors")
    print("=" * 60)

    manager = ScraperManager(use_mock=False)

    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
    ]

    for card in test_cards:
        print(f"\nCard: {card.name} ({card.set_name})")
        print("-" * 40)

        try:
            card_prices = manager.get_card_prices(card)

            # Find MTGMintCard prices
            mtgmintcard_prices = []
            other_prices = []

            for vendor, price_data in card_prices.prices.items():
                if "MTGMintCard" in vendor:
                    mtgmintcard_prices.append((vendor, price_data))
                else:
                    other_prices.append((vendor, price_data))

            # Display MTGMintCard prices
            if mtgmintcard_prices:
                print("MTGMintCard Prices:")
                for vendor, price_data in mtgmintcard_prices:
                    print(f"  {vendor}: ${price_data.price}")
                    if price_data.all_conditions.get("buylist_price"):
                        print(
                            f"    Buylist: ${price_data.all_conditions['buylist_price']}"
                        )
                    if price_data.all_conditions.get("sell_price"):
                        print(f"    Sell: ${price_data.all_conditions['sell_price']}")
            else:
                print("No MTGMintCard prices found")

            # Display other vendor prices
            if other_prices:
                print("\nOther Vendor Prices:")
                for vendor, price_data in other_prices:
                    print(f"  {vendor}: ${price_data.price}")
            else:
                print("\nNo other vendor prices found")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_mtgmintcard_integration()
    test_mtgmintcard_vs_other_vendors()
