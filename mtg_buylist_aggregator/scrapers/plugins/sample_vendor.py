from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper


class SampleVendorScraper(BaseScraper):
    def search_card(self, card):
        # Return None or a fake price for demonstration
        return None


def register_scrapers(manager_cls):
    manager_cls.register_scraper("Sample Vendor", SampleVendorScraper)
