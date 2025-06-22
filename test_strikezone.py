#!/usr/bin/env python3
"""Test script for StrikeZoneOnline scraper."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.strikezone import StrikeZoneScraper
from mtg_buylist_aggregator.models import Card


def test_strikezone_scraper():
    scraper = StrikeZoneScraper()
    card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)
    print("Testing StrikeZoneOnline Scraper for Rhystic Study (Prophecy)")
    print("-" * 60)
    price_data = scraper.search_card(card)
    if price_data:
        print(f"✓ Best Buylist Price: ${price_data.price}")
        print(f"  Condition: {price_data.condition}")
        print(f"  Quantity Limit: {price_data.quantity_limit}")
        print(f"  All Conditions:")
        for row in price_data.all_conditions["manual_rows"]:
            print(f"    {row['condition']}: ${row['price']} (Qty: {row['quantity']})")
    else:
        print("✗ No buylist price found")


if __name__ == "__main__":
    test_strikezone_scraper()
