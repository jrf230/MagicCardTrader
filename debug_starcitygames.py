#!/usr/bin/env python3
"""Debug Star City Games buylist page structure."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import re
import json

def debug_starcitygames_page():
    """Debug what's on the Star City Games buylist page for Rhystic Study."""
    print("=== Debugging Star City Games Buylist Page Structure ===\n")
    
    # Set up session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Try the main buylist page first
    base_url = "https://sellyourcards.starcitygames.com/mtg"
    print(f"=== Trying Base URL: {base_url} ===")
    
    try:
        resp = session.get(base_url, timeout=15)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Check page title
            title = soup.find("title")
            if title:
                print(f"Page Title: {title.get_text()}")
            
            # Look for any scripts that might contain API endpoints
            scripts = soup.find_all("script")
            print(f"Scripts found: {len(scripts)}")
            
            for i, script in enumerate(scripts):
                script_content = script.get_text()
                print(f"\nScript {i+1}:")
                print(f"Length: {len(script_content)} characters")
                
                # Look for API endpoints or configuration
                if "api" in script_content.lower():
                    print("  Contains 'api'")
                if "endpoint" in script_content.lower():
                    print("  Contains 'endpoint'")
                if "search" in script_content.lower():
                    print("  Contains 'search'")
                if "buylist" in script_content.lower():
                    print("  Contains 'buylist'")
                
                # Look for any URLs or endpoints
                urls = re.findall(r'https?://[^\s"\'<>]+', script_content)
                if urls:
                    print(f"  URLs found: {urls[:5]}...")  # Show first 5
            
            # Look for any forms or hidden inputs
            forms = soup.find_all("form")
            print(f"\nForms found: {len(forms)}")
            
            for form in forms:
                print(f"  Form action: {form.get('action', 'None')}")
                print(f"  Form method: {form.get('method', 'None')}")
                
                inputs = form.find_all("input")
                for inp in inputs:
                    print(f"    Input: {inp.get('name', 'None')} = {inp.get('value', 'None')}")
            
            # Try to find any data attributes or configuration
            all_elements = soup.find_all(attrs={"data-": True})
            print(f"\nElements with data attributes: {len(all_elements)}")
            
            for elem in all_elements[:5]:  # Show first 5
                data_attrs = {k: v for k, v in elem.attrs.items() if k.startswith('data-')}
                if data_attrs:
                    print(f"  {elem.name}: {data_attrs}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Try some common API endpoints
    print("\n=== Trying Common API Endpoints ===")
    api_endpoints = [
        "https://sellyourcards.starcitygames.com/api/search",
        "https://sellyourcards.starcitygames.com/api/buylist",
        "https://sellyourcards.starcitygames.com/api/mtg/search",
        "https://starcitygames.com/api/buylist",
        "https://starcitygames.com/api/search",
    ]
    
    for endpoint in api_endpoints:
        try:
            resp = session.get(endpoint, timeout=10)
            print(f"{endpoint}: {resp.status_code}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")
    
    # Try the old SCG site to see if it still works
    print("\n=== Trying Old SCG Site ===")
    try:
        old_url = "https://old.starcitygames.com/buylist/search/?search=Rhystic+Study"
        resp = session.get(old_url, timeout=15)
        print(f"Old site status: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = soup.get_text()
            print(f"Old site text length: {len(page_text)}")
            
            # Look for buylist table
            table = soup.find("table", class_="buylist-table")
            if table:
                print("✅ Found buylist table!")
                rows = table.find_all("tr")
                print(f"Table has {len(rows)} rows")
                
                # Show first few rows
                for i, row in enumerate(rows[:3]):
                    cells = row.find_all(["td", "th"])
                    print(f"  Row {i+1}: {len(cells)} cells")
                    for j, cell in enumerate(cells[:3]):
                        print(f"    Cell {j+1}: {cell.get_text()[:50]}...")
            else:
                print("❌ No buylist table found")
        
    except Exception as e:
        print(f"Old site error: {e}")

if __name__ == "__main__":
    debug_starcitygames_page() 