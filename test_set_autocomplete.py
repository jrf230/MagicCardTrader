#!/usr/bin/env python3
"""
Test script for set autocomplete functionality
"""

import requests
import json

def test_card_sets_api():
    """Test the card sets API endpoint"""
    print("Testing Card Sets API...")
    
    # Test with a card that has multiple printings
    card_name = "Lightning Bolt"
    
    try:
        response = requests.get(f"http://localhost:8080/api/card-sets/{card_name}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('sets', []))} sets for {card_name}")
            
            # Show first few sets
            for i, set_info in enumerate(data.get('sets', [])[:10]):
                print(f"  {i+1}. {set_info['name']} ({set_info['code']}) - {set_info['released_at'][:4]}")
                
            if len(data.get('sets', [])) > 10:
                print(f"  ... and {len(data.get('sets', [])) - 10} more sets")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

def test_search_autocomplete():
    """Test the search autocomplete API endpoint"""
    print("\nTesting Search Autocomplete API...")
    
    query = "cabal ritual"
    
    try:
        response = requests.get(f"http://localhost:8080/api/search-cards-autocomplete?q={query}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('cards', []))} cards for '{query}'")
            
            # Show first few cards
            for i, card in enumerate(data.get('cards', [])[:3]):
                print(f"  {i+1}. {card['name']} - {card['set_name']} ({card['set_code']})")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_card_sets_api()
    test_search_autocomplete() 