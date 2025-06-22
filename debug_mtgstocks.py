#!/usr/bin/env python3
"""Debug MTGStocks page structure."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re


def debug_mtgstocks_page():
    """Debug what's on the MTGStocks page for Rhystic Study."""
    print("=== Debugging MTGStocks Page Structure ===\n")

    # Set up session
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )

    # Search for Rhystic Study on MTGStocks
    search_term = "Rhystic Study"
    url = f"https://www.mtgstocks.com/prints?query={quote_plus(search_term)}"

    print(f"Searching URL: {url}\n")

    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Check page title
        title = soup.find("title")
        if title:
            print(f"Page Title: {title.get_text()}")

        # Check for any content
        page_text = soup.get_text()
        print(f"Page text length: {len(page_text)} characters")
        print(f"First 1000 chars: {page_text[:1000]}...")

        # Look for any prices
        prices = re.findall(r"\$(\d+\.?\d*)", page_text)
        print(f"\nAll prices found: {prices[:20]}...")  # Show first 20

        # Look for bid/offer indicators
        print("\n=== Bid/Offer Indicators ===")
        bid_offer_indicators = [
            "bid",
            "offer",
            "wants",
            "offers",
            "buy",
            "sell",
            "market",
        ]

        for indicator in bid_offer_indicators:
            if indicator in page_text.lower():
                print(f"Found '{indicator}' in page text")

        # Look for price elements
        print("\n=== Price Elements ===")
        price_elements = soup.find_all(
            ["span", "div", "td"],
            class_=re.compile(r"price|bid|offer|wants|offers", re.I),
        )
        print(f"Found {len(price_elements)} price elements")

        for i, element in enumerate(price_elements[:10]):  # Show first 10
            print(f"\nPrice Element {i+1}:")
            print(f"Tag: {element.name}")
            print(f"Classes: {element.get('class', 'None')}")
            print(f"Text: {element.get_text()[:100]}...")

        # Look for tables
        print("\n=== Tables ===")
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables")

        for i, table in enumerate(tables[:3]):  # Show first 3
            print(f"\nTable {i+1}:")
            rows = table.find_all("tr")
            print(f"Has {len(rows)} rows")

            for j, row in enumerate(rows[:3]):  # Show first 3 rows
                cells = row.find_all(["td", "th"])
                print(f"  Row {j+1}: {len(cells)} cells")
                for k, cell in enumerate(cells[:3]):  # Show first 3 cells
                    print(f"    Cell {k+1}: {cell.get_text()[:50]}...")

        # Look for any forms or search elements
        print("\n=== Forms and Search ===")
        forms = soup.find_all("form")
        print(f"Forms found: {len(forms)}")

        inputs = soup.find_all("input")
        print(f"Input fields found: {len(inputs)}")

        # Look for any JavaScript that might load content
        scripts = soup.find_all("script")
        print(f"Scripts found: {len(scripts)}")

        # Check if this looks like a search results page
        if "rhystic study" in page_text.lower():
            print("\n✅ Found 'rhystic study' in page text")
        else:
            print("\n❌ Did not find 'rhystic study' in page text")

        # Look for any card-specific elements
        print("\n=== Card Elements ===")
        card_elements = soup.find_all(
            ["div", "span", "tr"], class_=re.compile(r"card|print|result", re.I)
        )
        print(f"Found {len(card_elements)} card elements")

        for i, element in enumerate(card_elements[:5]):  # Show first 5
            print(f"\nCard Element {i+1}:")
            print(f"Tag: {element.name}")
            print(f"Classes: {element.get('class', 'None')}")
            print(f"Text: {element.get_text()[:200]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    debug_mtgstocks_page()
