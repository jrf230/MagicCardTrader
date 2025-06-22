#!/usr/bin/env python3
"""Test script for Nerd Rage Gaming scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mtg_buylist_aggregator.scrapers.nerdragegaming import NerdRageGamingScraper
from mtg_buylist_aggregator.models import Card

def test_nerdragegaming_scraper():
    """Test the Nerd Rage Gaming scraper with various cards."""
    
    scraper = NerdRageGamingScraper()
    
    # Test cards
    test_cards = [
        Card(name="Rhystic Study", set_name="Prophecy", quantity=1),
        Card(name="Sol Ring", set_name="Commander 2021", quantity=1),
        Card(name="Demonic Tutor", set_name="Revised Edition", quantity=1),
        Card(name="Lightning Bolt", set_name="Revised Edition", quantity=1),
        Card(name="Ancient Tomb", set_name="Zendikar Rising Expeditions", quantity=1),
    ]
    
    print("Testing Nerd Rage Gaming Scraper")
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
                
                # Check if we have both cash and credit prices
                if buylist_data.all_conditions.get('cash_price') and buylist_data.all_conditions.get('credit_price'):
                    print(f"  Cash: ${buylist_data.all_conditions['cash_price']}")
                    print(f"  Credit: ${buylist_data.all_conditions['credit_price']}")
                    print(f"  Trade-in Bonus: {buylist_data.all_conditions['trade_in_bonus']*100}%")
                    print(f"  TCG Low Reference: ${buylist_data.all_conditions['tcg_low_reference']}")
                    print(f"  Note: {buylist_data.all_conditions['note']}")
            else:
                print("✗ No buylist price found")
            
            # Test sell price separately
            sell_data = scraper._get_sell_price(card)
            if sell_data:
                print(f"✓ Sell Price: ${sell_data.price}")
                print(f"  Vendor: {sell_data.vendor}")
            else:
                print("✗ No sell price found")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

def test_nerdragegaming_with_sell_price():
    """Test the combined buylist and sell price functionality."""
    
    scraper = NerdRageGamingScraper()
    
    test_card = Card(name="Rhystic Study", set_name="Prophecy", quantity=1)
    
    print("\nTesting Nerd Rage Gaming with combined buylist/sell prices")
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
            print(f"  Cash: ${buylist.all_conditions['cash_price']}")
            print(f"  Credit: ${buylist.all_conditions['credit_price']}")
            print(f"  Trade-in Bonus: {buylist.all_conditions['trade_in_bonus']*100}%")
        else:
            print("✗ No buylist data")
            
        if combined_data["sell"]:
            sell = combined_data["sell"]
            print(f"✓ Sell: ${sell.price} from {sell.vendor}")
            print(f"  Condition: {sell.condition}")
        else:
            print("✗ No sell data")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_nerdragegaming_scraper()
    test_nerdragegaming_with_sell_price() 