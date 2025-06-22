#!/usr/bin/env python3
"""Test Star City Games buylist scraper specifically."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.starcitygames import StarCityGamesScraper
from mtg_buylist_aggregator.models import Card
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_starcitygames_buylist():
    """Test Star City Games buylist scraper."""
    print("=== Testing Star City Games Buylist (What They Pay) ===\n")
    
    scraper = StarCityGamesScraper()
    
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
                print(f"   Price Type: {price_data.all_conditions.get('price_type', 'unknown')}")
                
                # Show additional info based on price type
                if price_data.all_conditions.get('price_type') == 'buylist_element_match':
                    buylist_prices = price_data.all_conditions.get('buylist_prices', [])
                    print(f"   Buylist Prices Found: {buylist_prices}")
                
                print(f"   Search URL: {price_data.all_conditions.get('search_url', 'N/A')}")
            else:
                print(f"❌ {card.name}: No buylist price found")
            
            print()
            
        except Exception as e:
            print(f"❌ {card.name}: Error - {e}")
            print()
    
    print("=== Buylist Test Complete ===")

if __name__ == "__main__":
    test_starcitygames_buylist() 