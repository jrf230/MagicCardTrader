from flask import Flask, render_template, jsonify, request, redirect, url_for
from mtg_buylist_aggregator.card_manager import CardManager
from mtg_buylist_aggregator.scrapers.scraper_manager import ScraperManager
from mtg_buylist_aggregator.enhanced_price_analyzer import EnhancedPriceAnalyzer
from mtg_buylist_aggregator.hot_card_detector import HotCardDetector
from mtg_buylist_aggregator.recommendation_engine import RecommendationEngine
from mtg_buylist_aggregator.price_history import PriceHistory
from mtg_buylist_aggregator.config import Config
from mtg_buylist_aggregator.api_service import get_api_service
from mtg_buylist_aggregator.database import get_database
import json
from datetime import datetime
from mtg_buylist_aggregator.models import Card, FoilTreatment, Condition
import requests
import logging
import re
from html import escape
from collections import defaultdict
import time
from mtg_buylist_aggregator.scrapers.cardkingdom import CardKingdomScraper
from urllib.parse import quote_plus
import threading
from functools import lru_cache
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Global configuration
app.config["SECRET_KEY"] = "mtg-trader-secret-key-2024"

# Initialize API service
api_service = get_api_service()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("web_dashboard.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Simple rate limiting
class RateLimiter:
    def __init__(self, max_requests=60, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip):
        now = time.time()
        client_requests = self.requests[client_ip]

        # Remove old requests outside the window
        client_requests[:] = [
            req_time
            for req_time in client_requests
            if now - req_time < self.window_seconds
        ]

        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False

        # Add current request
        client_requests.append(now)
        return True


# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 requests per minute

# API usage tracking
api_stats = {
    "total_requests": 0,
    "errors": 0,
    "endpoints": defaultdict(int),
    "last_reset": datetime.now(),
}


def log_api_request(endpoint, success=True, error=None):
    """Log API request for monitoring"""
    api_stats["total_requests"] += 1
    api_stats["endpoints"][endpoint] += 1

    if not success:
        api_stats["errors"] += 1

    if error:
        logger.error(f"API Error in {endpoint}: {error}")
    else:
        logger.info(f"API Request: {endpoint} - {'Success' if success else 'Failed'}")


def get_api_stats():
    """Get API usage statistics"""
    return {
        "total_requests": api_stats["total_requests"],
        "errors": api_stats["errors"],
        "success_rate": (
            (api_stats["total_requests"] - api_stats["errors"])
            / max(api_stats["total_requests"], 1)
        )
        * 100,
        "endpoints": dict(api_stats["endpoints"]),
        "uptime": (datetime.now() - api_stats["last_reset"]).total_seconds(),
    }


def check_rate_limit():
    """Decorator to check rate limiting"""
    client_ip = request.remote_addr
    if not rate_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
    return None


@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html")


@app.route("/collection")
def collection():
    """Collection management page"""
    try:
        manager = CardManager()
        cards = manager.list_cards()
        return render_template("collection.html", cards=cards)
    except Exception as e:
        return render_template("error.html", error=str(e))


@app.route("/market-analysis")
def market_analysis():
    """Market analysis page"""
    return render_template("market_analysis.html")


@app.route("/hot-cards")
def hot_cards():
    """Hot cards page"""
    return render_template("hot_cards.html")


@app.route("/recommendations")
def recommendations():
    """Recommendations page"""
    return render_template("recommendations.html")


@app.route("/vendors")
def vendors():
    """Vendor health page"""
    return render_template("vendors.html")


@app.route("/test")
def test():
    return "<h1>Hello, Flask is working!</h1>"


@app.route("/card-details")
def card_details():
    """Single card details page"""
    return render_template("card_details.html")


# API Endpoints


@app.route("/api/health")
def api_health():
    """Health check endpoint"""
    try:
        # Check if collection file exists and is readable
        manager = CardManager()
        cards = manager.list_cards()

        # Check if price cache is accessible
        from mtg_buylist_aggregator.price_cache import PriceCache

        price_cache = PriceCache()
        cache_status = price_cache.get_cache_status()

        # Get API stats
        stats = get_api_stats()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "collection": {"card_count": len(cards), "accessible": True},
            "price_cache": {
                "status": "healthy" if cache_status["total_cards"] > 0 else "empty",
                "cached_cards": cache_status["total_cards"],
                "last_updated": cache_status.get("last_updated", "Never"),
            },
            "api_stats": stats,
            "version": "1.0.0",
        }

        log_api_request("health", success=True)
        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        log_api_request("health", success=False, error=str(e))
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/api/collection")
def api_collection():
    """Get collection data"""
    try:
        manager = CardManager()
        cards = manager.list_cards()
        return jsonify(
            {"cards": [card.__dict__ for card in cards], "total_cards": len(cards)}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market-analysis")
def api_market_analysis():
    """Get enhanced market analysis data"""
    try:
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        analysis_data = api_service.get_market_analysis(force_refresh=force_refresh)

        log_api_request("market_analysis", success=True)
        return jsonify(analysis_data)

    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        log_api_request("market_analysis", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/hot-cards")
def api_hot_cards():
    """Get hot cards data"""
    try:
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        hot_cards_data = api_service.get_hot_cards(force_refresh=force_refresh)

        log_api_request("hot_cards", success=True)
        return jsonify(hot_cards_data)

    except Exception as e:
        logger.error(f"Hot cards error: {e}")
        log_api_request("hot_cards", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations")
def api_recommendations():
    """Get recommendations data"""
    try:
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        recommendations_data = api_service.get_recommendations(
            force_refresh=force_refresh
        )

        log_api_request("recommendations", success=True)
        return jsonify(recommendations_data)

    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        log_api_request("recommendations", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/vendors")
def api_vendors():
    """Get vendor health data"""
    try:
        vendors_data = api_service.get_vendors_data()

        log_api_request("vendors", success=True)
        return jsonify(vendors_data)

    except Exception as e:
        logger.error(f"Vendors error: {e}")
        log_api_request("vendors", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/add-card", methods=["POST"])
def api_add_card():
    """Add a card to the collection"""
    # Check rate limit
    rate_limit_error = check_rate_limit()
    if rate_limit_error:
        return rate_limit_error

    try:
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ["name", "set_name", "quantity", "foil"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Sanitize and validate input
        card_name = sanitize_input(data.get("name", "")).strip().title()
        set_name = sanitize_input(data.get("set_name", "")).strip()

        # Validate card name
        is_valid_name, name_error = validate_card_name(card_name)
        if not is_valid_name:
            return jsonify({"error": name_error}), 400

        # Validate set name
        is_valid_set, set_error = validate_set_name(set_name)
        if not is_valid_set:
            return jsonify({"error": set_error}), 400

        # Validate quantity
        try:
            quantity = int(data.get("quantity", 0))
            if quantity < 1 or quantity > 1000:
                return jsonify({"error": "Quantity must be between 1 and 1000"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Quantity must be a valid number"}), 400

        # Validate foil status
        foil = data.get("foil", False)
        if not isinstance(foil, bool):
            return jsonify({"error": "Foil must be a boolean value"}), 400

        # Create card object
        card = Card(
            name=card_name,
            set_name=set_name,
            quantity=quantity,
            foil_treatment=FoilTreatment.FOIL if foil else FoilTreatment.NONFOIL,
            condition=data.get("condition", "Near Mint"),
        )

        # Add to collection via API service
        result = api_service.add_card(card)

        if result["success"]:
            log_api_request("add_card", success=True)
            return jsonify(result)
        else:
            log_api_request("add_card", success=False, error=result["error"])
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error adding card: {e}")
        log_api_request("add_card", success=False, error=str(e))
        return jsonify({"error": "Internal server error. Please try again."}), 500


@app.route("/api/remove-card", methods=["POST"])
def api_remove_card():
    """Remove a card from collection"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        name = data.get("name", "").strip()
        set_name = data.get("set_name", "").strip()
        foil = data.get("foil", False)
        quantity = data.get("quantity")

        if not name or not set_name:
            return jsonify({"error": "Card name and set name are required"}), 400

        # Remove card via API service
        result = api_service.remove_card(name, set_name, foil, quantity)

        if result["success"]:
            log_api_request("remove_card", success=True)
            return jsonify(result)
        else:
            log_api_request("remove_card", success=False, error=result["error"])
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error removing card: {e}")
        log_api_request("remove_card", success=False, error=str(e))
        return jsonify({"error": "Internal server error. Please try again."}), 500


@app.route("/api/cache-status")
def api_cache_status():
    """Get cache status information"""
    try:
        cache_status = api_service.get_cache_status()

        log_api_request("cache_status", success=True)
        return jsonify(cache_status)

    except Exception as e:
        logger.error(f"Cache status error: {e}")
        log_api_request("cache_status", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/collection-prices")
def api_collection_prices():
    """Get collection with current prices"""
    try:
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        collection_data = api_service.get_collection_data(force_refresh=force_refresh)

        log_api_request("collection_prices", success=True)
        return jsonify(collection_data)

    except Exception as e:
        logger.error(f"Collection prices error: {e}")
        log_api_request("collection_prices", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-price-cache", methods=["POST"])
def api_update_price_cache():
    """Force update all prices (called when user clicks 'Update Prices')"""
    try:
        result = api_service.force_price_update()

        log_api_request("update_price_cache", success=True)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Price cache update error: {e}")
        log_api_request("update_price_cache", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/search-cards")
def api_search_cards():
    """Search for cards by name, set, rarity using Scryfall API"""
    try:
        query = request.args.get("q", "").strip()
        set_name = request.args.get("set", "").strip()
        rarity = request.args.get("rarity", "").strip()

        if not query and not set_name and not rarity:
            return jsonify({"error": "At least one search parameter is required"}), 400

        # Build Scryfall search query
        search_parts = []
        
        if query:
            # Use exact name search for better results
            search_parts.append(f'!"{query}"')
        
        if set_name:
            search_parts.append(f'set:"{set_name}"')
        
        if rarity:
            search_parts.append(f'rarity:"{rarity}"')
        
        search_query = " ".join(search_parts)
        
        # Use Scryfall search API
        scryfall_url = f"https://api.scryfall.com/cards/search?q={quote_plus(search_query)}&unique=prints"
        response = requests.get(scryfall_url, timeout=10)
        
        if response.status_code == 404:
            # No results found
            return jsonify({"cards": []})
        
        response.raise_for_status()
        data = response.json()
        
        cards = []
        if "data" in data:
            for card in data["data"]:
                cards.append({
                    "name": card["name"],
                    "set_name": card["set_name"],
                    "set_code": card["set"],
                    "rarity": card["rarity"].title(),
                    "image_url": card.get("image_uris", {}).get("small", ""),
                    "released_at": card.get("released_at", ""),
                    "collector_number": card.get("collector_number", ""),
                    "artist": card.get("artist", "")
                })
        
        # Sort by set release date (newest first)
        cards.sort(key=lambda x: x["released_at"], reverse=True)
        
        return jsonify({"cards": cards})

    except requests.RequestException as e:
        logger.error(f"Scryfall search error: {e}")
        return jsonify({"error": "Failed to search cards. Please try again."}), 500
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/card-details")
def api_card_details():
    """Get details and prices for a single card."""
    try:
        name = request.args.get("name")
        set_name = request.args.get("set")
        foil = request.args.get("foil", "false").lower() == "true"
        condition = request.args.get("condition", None)
        
        if not name or not set_name:
            return jsonify({"error": "Card name and set are required"}), 400
            
        # Normalize name and set
        name = name.strip().title()
        set_name = set_name.strip().title()
        
        # Build Card object
        from mtg_buylist_aggregator.models import Card, Condition

        card_kwargs = dict(name=name, set_name=set_name, quantity=1)
        if condition:
            card_kwargs["condition"] = Condition(condition)
        card = Card(**card_kwargs)
        card.foil = foil
        
        # Get price data from all vendors
        scraper_manager = ScraperManager(use_mock=False)
        card_prices = scraper_manager.get_collection_prices([card])

        # Initialize default response structure
        vendors_data = []
        best_bid = None
        best_vendor = None
        
        if card_prices and len(card_prices) > 0:
            card_price_data = card_prices[0]
            
            # Prepare vendor data
            for vendor, price_data_list in card_price_data.prices.items():
                # price_data_list is now a list of PriceData objects
                for price_data in price_data_list:
                    # Only include prices matching the foil status
                    if card.is_foil() != (
                        getattr(price_data, "foil", False)
                        or getattr(price_data, "foil_treatment", None) == "Foil"
                    ):
                        continue
                    
                    # Use the price directly since we don't have all_conditions anymore
                    price = price_data.price if price_data.price else 0
                    
                    # Determine price type and set bid/ask/mid accordingly
                    price_type = getattr(price_data, 'price_type', 'unknown')
                    bid = None
                    ask = None
                    mid = None
                    
                    if 'bid' in price_type.lower():
                        bid = price
                    elif 'offer' in price_type.lower() or 'ask' in price_type.lower():
                        ask = price
                    else:
                        # Default to mid price for unknown types
                        mid = price
                    
                    vendors_data.append(
                        {
                            "vendor": vendor,
                            "bid": bid,
                            "ask": ask,
                            "mid": mid,
                            "condition": price_data.condition,
                            "last_updated": (
                                price_data.last_price_update.isoformat()
                                if price_data.last_price_update
                                else None
                            ),
                        }
                    )
            
            # Get best bid info
            if card_price_data.best_bid:
                best_bid = card_price_data.best_bid.price
                best_vendor = card_price_data.best_bid.vendor

        # Get historical data
        history = PriceHistory()
        historical_data = history.get_card_history(name, set_name, days=30)

        # Add Card Kingdom retail prices by condition
        retail_prices_by_condition = {}
        try:
            ck_scraper = CardKingdomScraper()
            retail_prices = ck_scraper.get_retail_prices_by_condition(card)
            retail_prices_by_condition = {k: v.dict() for k, v in retail_prices.items()}
        except Exception as e:
            logger.warning(f"Failed to get Card Kingdom retail prices for {name}: {e}")

        response = {
            "card": {
                "name": card.name,
                "set_name": card.set_name,
                "foil": foil,
                "rarity": card.rarity.value if card.rarity else "Unknown",
            },
            "current_prices": {
                "best_bid": best_bid,
                "best_vendor": best_vendor,
                "vendors": vendors_data,
            },
            "historical_data": historical_data,
            "retail_prices_by_condition": retail_prices_by_condition,
        }
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in card details API: {e}")
        return jsonify({"error": f"Failed to get card details: {str(e)}"}), 500


@app.route("/api/search-cards-autocomplete")
def api_search_cards_autocomplete():
    """Autocomplete for card names using Scryfall."""
    query = request.args.get("query", "")
    if not query or len(query) < 3:
        return jsonify({"cards": []})

    try:
        # Use Scryfall's autocomplete endpoint
        scryfall_url = (
            f"https://api.scryfall.com/cards/autocomplete?q={quote_plus(query)}"
        )
        response = requests.get(scryfall_url, timeout=5)
        response.raise_for_status()
        data = response.json().get("data", [])

        # Filter results to only include exact matches for the card name part
        # This prevents "Cabal Pit" from showing for "Cabal Ritual"
        filtered_data = [
            card_name for card_name in data if query.lower() in card_name.lower()
        ]

        # For more accuracy, once the query is long enough, switch to a search
        # that finds all printings of a single card.
        if len(filtered_data) == 1 and query.lower() == filtered_data[0].lower():
            return api_get_card_printings(query)

        return jsonify({"cards": filtered_data[:10]})  # Return top 10

    except requests.RequestException as e:
        logger.error(f"Scryfall autocomplete error: {e}")
        return jsonify({"error": "Failed to fetch card suggestions."}), 500


def api_get_card_printings(card_name):
    """Get all printings of a specific card."""
    try:
        search_url = f'https://api.scryfall.com/cards/search?q=!"{quote_plus(card_name)}"&unique=prints'
        response = requests.get(search_url, timeout=5)
        response.raise_for_status()

        cards = response.json().get("data", [])

        # Format for display
        suggestions = [
            {
                "name": card["name"],
                "set_name": card["set_name"],
                "set_code": card["set"],
                "rarity": card["rarity"].title(),
            }
            for card in cards
        ]

        return jsonify({"cards": suggestions, "is_printings": True})

    except requests.RequestException:
        # Fallback to simple autocomplete if the exact search fails
        return api_search_cards_autocomplete()


@app.route("/api/card-sets/<card_name>")
def get_card_sets(card_name):
    """Get all sets where a card appears"""
    try:
        # Use Scryfall search to find all printings
        search_url = f"https://api.scryfall.com/cards/search?q=!%22{card_name}%22"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()

        data = response.json()
        sets = []

        if "data" in data:
            for card in data["data"]:
                set_info = {
                    "name": card.get("set_name", ""),
                    "code": card.get("set", ""),
                    "released_at": card.get("released_at", ""),
                    "rarity": card.get("rarity", ""),
                }
                if set_info not in sets:
                    sets.append(set_info)

        # Sort by release date (newest first)
        sets.sort(key=lambda x: x["released_at"], reverse=True)

        return jsonify({"sets": sets})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def sanitize_input(text, max_length=100):
    """Sanitize user input to prevent XSS and injection attacks."""
    if not text:
        return ""

    # Convert to string and strip whitespace
    text = str(text).strip()

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', "", text)

    # HTML escape
    text = escape(text)

    return text


def validate_card_name(name):
    """Validate card name format."""
    if not name or len(name.strip()) < 2:
        return False, "Card name must be at least 2 characters long"

    if len(name.strip()) > 100:
        return False, "Card name is too long"

    # Check for valid characters (letters, numbers, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z0-9\s\-\'\.]+$", name):
        return False, "Card name contains invalid characters"

    return True, ""


def validate_set_name(set_name):
    """Validate set name format."""
    if not set_name or len(set_name.strip()) < 2:
        return False, "Set name must be at least 2 characters long"

    if len(set_name.strip()) > 100:
        return False, "Set name is too long"

    # Check for valid characters
    if not re.match(r"^[a-zA-Z0-9\s\-\'\.]+$", set_name):
        return False, "Set name contains invalid characters"

    return True, ""


@app.route("/api/dashboard")
def api_dashboard():
    """Get all dashboard data in a single optimized call"""
    try:
        force_refresh = request.args.get("force_refresh", "false").lower() == "true"
        dashboard_data = api_service.get_dashboard_data(force_refresh=force_refresh)

        log_api_request("dashboard", success=True)
        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        log_api_request("dashboard", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/api/clear-cache", methods=["POST"])
def api_clear_cache():
    """Clear the dashboard cache to force fresh data"""
    try:
        result = api_service.clear_cache()

        log_api_request("clear_cache", success=True)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        log_api_request("clear_cache", success=False, error=str(e))
        return jsonify({"error": str(e)}), 500


# Initialize background scheduler for periodic refresh
scheduler = BackgroundScheduler()


def refresh_prices_and_analytics():
    logger.info("[Scheduler] Running periodic price and analytics refresh...")
    try:
        api_service.force_price_update()
        api_service.get_dashboard_data(force_refresh=True)
        api_service.get_market_analysis(force_refresh=True)
        api_service.get_hot_cards(force_refresh=True)
        api_service.get_recommendations(force_refresh=True)
        logger.info("[Scheduler] Price and analytics refresh complete.")
    except Exception as e:
        logger.error(f"[Scheduler] Error during periodic refresh: {e}")


# Schedule the job every 6 hours
scheduler.add_job(
    refresh_prices_and_analytics,
    "interval",
    hours=6,
    id="refresh_job",
    replace_existing=True,
)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
