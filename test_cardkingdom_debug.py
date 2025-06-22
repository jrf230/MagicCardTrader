#!/usr/bin/env python3

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def debug_card_kingdom_search():
    print("Debugging Card Kingdom search for Cabal Ritual...")
    
    # Test retail search first since it found results
    card_name = quote_plus("Cabal Ritual")
    retail_url = f"https://www.cardkingdom.com/catalog/search?search=header&filter%5Bname%5D={card_name}"
    print(f"Retail URL: {retail_url}")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.cardkingdom.com/",
    })
    
    try:
        resp = session.get(retail_url, timeout=20)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        product_items = soup.select("div.productItemWrapper")
        print(f"Found {len(product_items)} product items")
        
        for i, item in enumerate(product_items[:3]):  # Show first 3
            print(f"\n=== Product {i+1} ===")
            
            # Look for all possible title elements
            title_selectors = [
                "span.productDetailTitle",
                "div.productDetailTitle", 
                "h3.productDetailTitle",
                "a.productDetailTitle",
                ".productDetailTitle"
            ]
            
            title_found = False
            for selector in title_selectors:
                title_div = item.select_one(selector)
                if title_div:
                    title_text = title_div.get_text(strip=True)
                    print(f"Title ({selector}): {title_text}")
                    title_found = True
                    break
            
            if not title_found:
                print("No title found with any selector")
            
            # Look for set information in other elements
            set_selectors = [
                "div.productDetailSubtitle",
                "span.productDetailSubtitle",
                ".productDetailSubtitle",
                "div.set-name",
                ".set-name",
                "span.set-name"
            ]
            
            for selector in set_selectors:
                set_div = item.select_one(selector)
                if set_div:
                    set_text = set_div.get_text(strip=True)
                    print(f"Set info ({selector}): {set_text}")
            
            # Look for any text that might contain set information
            all_text = item.get_text()
            if "torment" in all_text.lower():
                print("✓ Found 'torment' in item text")
            if "vintage masters" in all_text.lower():
                print("✓ Found 'vintage masters' in item text")
            if "mystery booster" in all_text.lower():
                print("✓ Found 'mystery booster' in item text")
            
            # Look for condition items
            condition_items = item.select("div.itemContentWrapper")
            print(f"Found {len(condition_items)} condition items")
            
            for j, cond_item in enumerate(condition_items):
                print(f"  Condition item {j+1}:")
                
                # Look for condition
                condition_div = cond_item.select_one("div.style")
                if condition_div:
                    condition_text = condition_div.get_text(strip=True)
                    print(f"    Condition: {condition_text}")
                
                # Look for price
                price_div = cond_item.select_one("span.price")
                if price_div:
                    price_text = price_div.get_text(strip=True)
                    print(f"    Price: {price_text}")
                
                # Look for any other text
                cond_text = cond_item.get_text(strip=True)
                if "torment" in cond_text.lower():
                    print(f"    ✓ Contains 'torment'")
                if "vintage masters" in cond_text.lower():
                    print(f"    ✓ Contains 'vintage masters'")
                if "mystery booster" in cond_text.lower():
                    print(f"    ✓ Contains 'mystery booster'")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_card_kingdom_search() 