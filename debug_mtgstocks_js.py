#!/usr/bin/env python3
"""Debug MTGStocks with JavaScript rendering."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re
import time


def debug_mtgstocks_with_js():
    """Debug MTGStocks with JavaScript rendering attempt."""
    print("=== Debugging MTGStocks with JavaScript ===\n")

    # Set up session
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://www.mtgstocks.com/",
        }
    )

    # Try different URL patterns for MTGStocks
    test_urls = [
        "https://www.mtgstocks.com/prints?query=Rhystic+Study",
        "https://www.mtgstocks.com/cards/Rhystic-Study",
        "https://www.mtgstocks.com/cards/rhystic-study",
        "https://www.mtgstocks.com/prints/Rhystic-Study",
    ]

    for i, url in enumerate(test_urls):
        print(f"Testing URL {i+1}: {url}")

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Check page title
            title = soup.find("title")
            if title:
                print(f"  Title: {title.get_text()}")

            # Check for any content
            page_text = soup.get_text()
            print(f"  Page length: {len(page_text)} chars")

            # Look for key sections
            if "SELLING OFFERS" in page_text:
                print("  ✅ Found SELLING OFFERS section")
            if "BUYING OFFERS" in page_text:
                print("  ✅ Found BUYING OFFERS section")
            if "Average Values" in page_text:
                print("  ✅ Found Average Values section")

            # Look for any prices
            prices = re.findall(r"\$(\d+\.?\d*)", page_text)
            if prices:
                print(f"  Found {len(prices)} prices: {prices[:10]}...")
            else:
                print("  ❌ No prices found")

            # Look for JavaScript that might load content
            scripts = soup.find_all("script")
            print(f"  Found {len(scripts)} scripts")

            # Look for any API endpoints or data in scripts
            for script in scripts:
                if script.string:
                    script_text = script.string
                    if "api" in script_text.lower() or "fetch" in script_text.lower():
                        print("  Found potential API calls in script")
                        # Look for URLs in the script
                        urls = re.findall(r'["\']([^"\']*api[^"\']*)["\']', script_text)
                        if urls:
                            print(f"    API URLs: {urls[:3]}...")

            print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()

    print("=== JavaScript Debug Complete ===")


if __name__ == "__main__":
    debug_mtgstocks_with_js()
