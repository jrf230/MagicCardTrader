#!/usr/bin/env python3
"""Debug Card Kingdom page structure."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re


def debug_cardkingdom_page():
    """Debug what's on the Card Kingdom page for Rhystic Study."""
    print("=== Debugging Card Kingdom Page Structure ===\n")

    # Set up session
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )

    # Search for just "Rhystic Study" (broader search)
    search_term = "Rhystic Study"
    encoded_search = quote_plus(search_term)
    url = f"https://www.cardkingdom.com/catalog/search?search=header&filter%5Bname%5D={encoded_search}"

    print(f"Searching URL: {url}\n")

    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Check if we got results
        if "No results were found" in soup.get_text():
            print("❌ No results found for the search")
            return

        # Look for product containers
        print("=== Looking for Product Containers ===")
        product_containers = soup.find_all(
            ["div", "tr", "li"], class_=re.compile(r"product|item|card", re.I)
        )
        print(f"Found {len(product_containers)} product containers")

        for i, container in enumerate(product_containers[:10]):  # Show first 10
            print(f"\nContainer {i+1}:")
            print(f"Classes: {container.get('class', 'None')}")
            container_text = container.get_text()
            print(f"Text preview: {container_text[:300]}...")

            # Check if this container has "prophecy" in it
            if "prophecy" in container_text.lower():
                print("  ✅ CONTAINS PROPHECY!")

                # Look for prices in this container
                prices = re.findall(r"\$(\d+\.?\d*)", container_text)
                if prices:
                    print(f"  Prices found: {prices}")

                # Look for buylist indicators
                buylist_indicators = [
                    "buylist",
                    "buy list",
                    "we buy",
                    "we'll buy",
                    "buying for",
                    "pay",
                    "cash for",
                    "trade-in",
                ]
                for indicator in buylist_indicators:
                    if indicator in container_text.lower():
                        print(f"  Found buylist indicator: '{indicator}'")

        # Look for tables
        print("\n=== Looking for Tables ===")
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables")

        for i, table in enumerate(tables[:5]):  # Show first 5
            print(f"\nTable {i+1}:")
            rows = table.find_all("tr")
            print(f"Has {len(rows)} rows")

            for j, row in enumerate(rows[:5]):  # Show first 5 rows
                cells = row.find_all(["td", "th"])
                row_text = row.get_text().lower()

                # Check if this row contains "prophecy"
                if "prophecy" in row_text:
                    print(f"  Row {j+1}: CONTAINS PROPHECY!")
                    print(f"    Full row text: {row.get_text()}")

                    # Look for prices in this row
                    prices = re.findall(r"\$(\d+\.?\d*)", row.get_text())
                    if prices:
                        print(f"    Prices found: {prices}")
                else:
                    print(f"  Row {j+1}: {len(cells)} cells")
                    for k, cell in enumerate(cells[:3]):  # Show first 3 cells
                        print(f"    Cell {k+1}: {cell.get_text()[:50]}...")

        # Look for all prices on the page
        print("\n=== All Prices Found ===")
        all_prices = re.findall(r"\$(\d+\.?\d*)", soup.get_text())
        print(f"Found {len(all_prices)} price matches")

        # Show unique prices sorted
        unique_prices = sorted(
            set([float(p) for p in all_prices if 0.01 <= float(p) <= 500])
        )
        print(f"Unique prices (0.01-500): {unique_prices[:30]}...")  # Show first 30

        # Look for buylist indicators
        print("\n=== Buylist Indicators ===")
        buylist_indicators = [
            "buylist",
            "buy list",
            "we buy",
            "we'll buy",
            "buying for",
            "pay",
            "cash for",
            "trade-in",
        ]

        for indicator in buylist_indicators:
            if indicator in soup.get_text().lower():
                print(f"Found '{indicator}' in page text")

        # Look for Prophecy set mentions
        print("\n=== Set Mentions ===")
        if "prophecy" in soup.get_text().lower():
            print("Found 'prophecy' in page text")

            # Find elements containing "prophecy"
            prophecy_elements = soup.find_all(string=re.compile("prophecy", re.I))
            print(f"Found {len(prophecy_elements)} elements containing 'prophecy'")

            for i, element in enumerate(prophecy_elements[:10]):
                print(f"  Element {i+1}: {element[:100]}...")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    debug_cardkingdom_page()
