#!/usr/bin/env python3
"""Test MTGStocks API endpoints."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from urllib.parse import quote_plus
import time


def test_mtgstocks_api():
    """Test potential MTGStocks API endpoints."""
    print("=== Testing MTGStocks API Endpoints ===\n")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://www.mtgstocks.com/",
        }
    )

    # Test potential API endpoints
    test_endpoints = [
        "https://www.mtgstocks.com/api/cards/Rhystic-Study",
        "https://www.mtgstocks.com/api/prints?query=Rhystic+Study",
        "https://www.mtgstocks.com/api/offers/Rhystic-Study",
        "https://www.mtgstocks.com/api/buylist/Rhystic-Study",
        "https://www.mtgstocks.com/api/prices/Rhystic-Study",
    ]

    for i, endpoint in enumerate(test_endpoints):
        print(f"Testing API endpoint {i+1}: {endpoint}")

        try:
            resp = session.get(endpoint, timeout=10)
            print(f"  Status: {resp.status_code}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"  ✅ JSON response: {json.dumps(data, indent=2)[:500]}...")
                except:
                    print(f"  📄 Text response: {resp.text[:200]}...")
            else:
                print(f"  ❌ Error response: {resp.text[:100]}...")

            print()
            time.sleep(1)  # Be respectful

        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()

    print("=== API Test Complete ===")


if __name__ == "__main__":
    test_mtgstocks_api()
