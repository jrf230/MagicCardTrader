#!/usr/bin/env python3
"""Test script to verify real data functionality."""

from mtg_buylist_aggregator.scrapers.scryfall import ScryfallScraper
from mtg_buylist_aggregator.models import Card
from mtg_buylist_aggregator.card_manager import CardManager


def test_scryfall_prices():
    """Test Scryfall scraper with real cards."""
    print("=== Testing Scryfall Real Price Data ===\n")

    scraper = ScryfallScraper()

    # Test cards from our collection
    test_cards = [
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1, foil=False),
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1, foil=True),
        Card(name="Demonic Tutor", set_name="Ultimate Masters", quantity=1, foil=False),
        Card(name="Counterspell", set_name="Commander 2013", quantity=1, foil=False),
        Card(name="Lightning Bolt", set_name="Magic 2010", quantity=1, foil=False),
    ]

    total_value = 0
    found_prices = 0

    for card in test_cards:
        result = scraper.search_card(card)
        if result and result.price:
            print(f"✅ {card.name} ({card.set_name}): ${result.price:.2f}")
            if card.foil:
                print(f"   Foil: {result.all_conditions.get('usd_foil', 'N/A')}")
            total_value += result.price
            found_prices += 1
        else:
            print(f"❌ {card.name} ({card.set_name}): No price found")

    print(f"\n📊 Summary:")
    print(f"   Cards with prices: {found_prices}/{len(test_cards)}")
    print(f"   Total value: ${total_value:.2f}")
    print(
        f"   Average price: ${total_value/found_prices:.2f}"
        if found_prices > 0
        else "   Average price: N/A"
    )


def test_collection_prices():
    """Test getting prices for actual collection."""
    print("\n=== Testing Collection Price Data ===\n")

    try:
        manager = CardManager()
        cards = manager.list_cards()

        if not cards:
            print("❌ No cards found in collection")
            return

        print(f"📚 Found {len(cards)} cards in collection")

        # Test with Scryfall only for now
        scraper = ScryfallScraper()

        total_value = 0
        found_prices = 0

        for card in cards[:5]:  # Test first 5 cards
            result = scraper.search_card(card)
            if result and result.price:
                print(f"✅ {card.name} ({card.set_name}): ${result.price:.2f}")
                total_value += result.price
                found_prices += 1
            else:
                print(f"❌ {card.name} ({card.set_name}): No price found")

        print(f"\n📊 Collection Test Summary:")
        print(f"   Cards with prices: {found_prices}/5")
        print(f"   Total value: ${total_value:.2f}")

    except Exception as e:
        print(f"❌ Error testing collection: {e}")


if __name__ == "__main__":
    test_scryfall_prices()
    test_collection_prices()
