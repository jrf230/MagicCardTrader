#!/usr/bin/env python3
"""Test script for BeatTheBuylist scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.beatthebuylist import BeatTheBuylistScraper
from mtg_buylist_aggregator.models import Card

def test_beatthebuylist_scraper():
    """Test the BeatTheBuylist scraper with various cards."""
    
    scraper = BeatTheBuylistScraper()
    
    # Test cards
    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Demonic Tutor", set_name="Revised Edition", quantity=1),
        Card(name="Lightning Bolt", set_name="Revised Edition", quantity=1),
        Card(name="Ancient Tomb", set_name="Zendikar Rising Expeditions", quantity=1),
    ]
    
    print("Testing BeatTheBuylist Scraper")
    print("=" * 50)
    
    for card in test_cards:
        print(f"\nTesting: {card.name} ({card.set_name})")
        print("-" * 40)
        
        try:
            # Test buylist price
            buylist_data = scraper.search_card(card)
            if buylist_data:
                print(f"✓ Buylist Price: ${buylist_data.price}")
                print(f"  Condition: {buylist_data.condition}")
                print(f"  Quantity Limit: {buylist_data.quantity_limit}")
                print(f"  Data Source: {buylist_data.all_conditions.get('data_source', 'web_scraped')}")
                
                # Check if we have both buylist and sell prices
                if buylist_data.all_conditions.get('buylist_price') and buylist_data.all_conditions.get('sell_price'):
                    print(f"  Buylist: ${buylist_data.all_conditions['buylist_price']}")
                    print(f"  Sell: ${buylist_data.all_conditions['sell_price']}")
                    print(f"  Vendors Aggregated: {len(buylist_data.all_conditions['vendors_aggregated'])}")
                    print(f"  Total Vendors Available: {buylist_data.all_conditions['total_vendors']}")
                    print(f"  Note: {buylist_data.all_conditions['note']}")
            else:
                print("✗ No buylist price found")
            
            # Test sell price separately
            sell_data = scraper._get_sell_price(card)
            if sell_data:
                print(f"✓ Sell Price: ${sell_data.price}")
                print(f"  Vendor: {sell_data.vendor}")
                print(f"  Vendors Aggregated: {len(sell_data.all_conditions['vendors_aggregated'])}")
            else:
                print("✗ No sell price found")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

def test_beatthebuylist_with_sell_price():
    """Test the combined buylist and sell price functionality."""
    
    scraper = BeatTheBuylistScraper()
    
    test_card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)
    
    print("\nTesting BeatTheBuylist with combined buylist/sell prices")
    print("=" * 60)
    
    try:
        combined_data = scraper.search_card_with_sell_price(test_card)
        
        print(f"Card: {test_card.name} ({test_card.set_name})")
        print("-" * 40)
        
        if combined_data["buylist"]:
            buylist = combined_data["buylist"]
            print(f"✓ Buylist: ${buylist.price} from {buylist.vendor}")
            print(f"  Condition: {buylist.condition}")
            print(f"  Quantity Limit: {buylist.quantity_limit}")
            print(f"  Buylist: ${buylist.all_conditions['buylist_price']}")
            print(f"  Sell: ${buylist.all_conditions['sell_price']}")
            print(f"  Vendors Aggregated: {len(buylist.all_conditions['vendors_aggregated'])}")
        else:
            print("✗ No buylist data")
            
        if combined_data["sell"]:
            sell = combined_data["sell"]
            print(f"✓ Sell: ${sell.price} from {sell.vendor}")
            print(f"  Condition: {sell.condition}")
            print(f"  Vendors Aggregated: {len(sell.all_conditions['vendors_aggregated'])}")
        else:
            print("✗ No sell data")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_aggregated_vendors():
    """Test the vendor aggregation functionality."""
    
    scraper = BeatTheBuylistScraper()
    
    print("\nTesting BeatTheBuylist Vendor Aggregation")
    print("=" * 50)
    
    vendors = scraper.get_aggregated_vendors()
    print(f"Total vendors aggregated: {len(vendors)}")
    print("\nVendors:")
    for i, vendor in enumerate(vendors, 1):
        print(f"  {i:2d}. {vendor}")

if __name__ == "__main__":
    test_beatthebuylist_scraper()
    test_beatthebuylist_with_sell_price()
    test_aggregated_vendors() 