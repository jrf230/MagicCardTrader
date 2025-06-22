#!/usr/bin/env python3
"""Test Star City Games API endpoints."""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from urllib.parse import quote_plus


def test_scg_api():
    """Test Star City Games API endpoints."""
    print("=== Testing Star City Games API Endpoints ===\n")

    # Set up session
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    )

    # Test the API endpoints that returned 200
    api_endpoints = [
        "https://sellyourcards.starcitygames.com/api/search",
        "https://sellyourcards.starcitygames.com/api/buylist",
        "https://sellyourcards.starcitygames.com/api/mtg/search",
    ]

    for endpoint in api_endpoints:
        print(f"=== Testing {endpoint} ===")

        try:
            # Try GET request first
            resp = session.get(endpoint, timeout=10)
            print(f"GET Status: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type', 'Unknown')}")

            if resp.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = resp.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)[:500]}...")
                except json.JSONDecodeError:
                    # If not JSON, show as text
                    print(f"Text Response: {resp.text[:500]}...")
            else:
                print(f"Response: {resp.text[:200]}...")

            print()

        except Exception as e:
            print(f"Error: {e}")
            print()

    # Try searching for a specific card via API
    print("=== Testing Search API with Rhystic Study ===")

    search_endpoints = [
        "https://sellyourcards.starcitygames.com/api/search?q=Rhystic+Study",
        "https://sellyourcards.starcitygames.com/api/mtg/search?q=Rhystic+Study",
        "https://sellyourcards.starcitygames.com/api/buylist?search=Rhystic+Study",
    ]

    for endpoint in search_endpoints:
        print(f"Testing: {endpoint}")

        try:
            resp = session.get(endpoint, timeout=10)
            print(f"Status: {resp.status_code}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Response: {json.dumps(data, indent=2)[:500]}...")
                except json.JSONDecodeError:
                    print(f"Response: {resp.text[:500]}...")
            else:
                print(f"Response: {resp.text[:200]}...")

            print()

        except Exception as e:
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    test_scg_api()
