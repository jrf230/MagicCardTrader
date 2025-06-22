#!/usr/bin/env python3
"""Debug TCG Player scraper."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import re
from urllib.parse import quote_plus
import time


def debug_tcgplayer():
    """Debug TCG Player search results."""
    print("=== Debugging TCG Player ===\n")

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

    # Test search
    search_query = "Rhystic Study Prophecy"
    search_url = "https://www.tcgplayer.com/search/all/product"
    params = {"q": search_query, "view": "grid"}

    print(f"Searching: {search_query}")
    print(f"URL: {search_url}")
    print(f"Params: {params}")
    print()

    try:
        response = session.get(search_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"Content Length: {len(response.text)} characters")

        # Check if we got redirected
        if response.history:
            print(f"Redirected from: {response.history[0].url}")

        # Look for any prices in the response
        html_content = response.text
        price_patterns = [
            r"\$(\d+\.?\d*)",  # Basic dollar pattern
            r'price["\']?\s*:\s*["\']?\$?(\d+\.?\d*)',  # JSON price pattern
            r'data-price["\']?\s*=\s*["\']?(\d+\.?\d*)',  # Data attribute pattern
            r"(\d+\.?\d*)\s*USD",  # USD pattern
        ]

        print("\n=== Price Patterns Found ===")
        for i, pattern in enumerate(price_patterns):
            matches = re.findall(pattern, html_content)
            if matches:
                print(f"Pattern {i+1}: Found {len(matches)} matches")
                print(f"  First 10 matches: {matches[:10]}")
            else:
                print(f"Pattern {i+1}: No matches")

        # Look for any text that might indicate the page content
        print(f"\n=== Page Content Sample ===")
        print(f"First 1000 chars: {html_content[:1000]}...")

        # Check if it's a JavaScript-heavy page
        if (
            "react" in html_content.lower()
            or "vue" in html_content.lower()
            or "angular" in html_content.lower()
        ):
            print("\n⚠️  This appears to be a JavaScript-heavy page")

        # Check for any error messages
        if "error" in html_content.lower() or "not found" in html_content.lower():
            print("\n⚠️  Possible error page detected")

        # Look for any card-related content
        if "rhystic study" in html_content.lower():
            print("\n✅ Found 'rhystic study' in page content")
        else:
            print("\n❌ Did not find 'rhystic study' in page content")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n=== Debug Complete ===")


if __name__ == "__main__":
    debug_tcgplayer()
