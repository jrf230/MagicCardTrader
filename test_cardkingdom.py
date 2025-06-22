#!/usr/bin/env python3
"""Test script for Card Kingdom scraper."""

from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from mtg_buylist_aggregator.models import Card


def test_cardkingdom():
    """Test Card Kingdom scraper with real cards."""
    print("=== Testing Card Kingdom Real Price Data ===\n")

    scraper = CardKingdomScraper()

    # Test cards from our collection
    test_cards = [
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1, foil=False),
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1, foil=True),
        Card(name="Demonic Tutor", set_name="Ultimate Masters", quantity=1, foil=False),
    ]

    total_value = 0
    found_prices = 0

    for card in test_cards:
        print(f"Searching for {card.name} ({card.set_name})...")
        result = scraper.search_card(card)
        if result and result.price:
            print(f"✅ {card.name} ({card.set_name}): ${result.price:.2f}")
            if result.all_conditions:
                print(
                    f"   Found prices: {result.all_conditions.get('found_prices', 'N/A')}"
                )
            total_value += result.price
            found_prices += 1
        else:
            print(f"❌ {card.name} ({card.set_name}): No price found")
        print()

    print(f"📊 Summary:")
    print(f"   Cards with prices: {found_prices}/{len(test_cards)}")
    print(f"   Total value: ${total_value:.2f}")
    print(
        f"   Average price: ${total_value/found_prices:.2f}"
        if found_prices > 0
        else "   Average price: N/A"
    )


if __name__ == "__main__":
    test_cardkingdom()
