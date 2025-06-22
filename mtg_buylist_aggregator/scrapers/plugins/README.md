# Vendor Scraper Plugins

To add a new vendor scraper as a plugin:

1. Create a new Python file in this directory (e.g., `myvendor.py`).
2. Define a class that inherits from `BaseScraper` and implements `search_card(self, card)`.
3. Define a `register_scrapers(manager_cls)` function that registers your scraper:

```python
from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper

class MyVendorScraper(BaseScraper):
    def search_card(self, card):
        # Implement vendor scraping logic
        return None

def register_scrapers(manager_cls):
    manager_cls.register_scraper('My Vendor', MyVendorScraper)
```

Your plugin will be auto-discovered and available in the CLI and web API. 