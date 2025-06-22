# Magic: The Gathering Buylist Aggregator

A comprehensive tool for tracking MTG card collections, analyzing price trends, detecting hot cards, and optimizing multi-vendor buylist strategies.

## 🚀 Features

### Core Functionality
- **Collection Management**: Add, remove, and track your MTG card collection
- **Multi-Vendor Price Comparison**: Compare buylist prices across 16+ vendors
- **Hot Card Detection**: Identify cards with significant price movements
- **Recommendation Engine**: Get buy/sell/hold recommendations based on market analysis
- **Collection Analytics**: Detailed insights into your collection's value and performance

### Advanced Features
- **Enhanced Market Analysis**: Comprehensive market insights using multiple data sources
- **Price Trend Detection**: Track price movements and volatility
- **Risk Assessment**: Evaluate investment risk based on price stability
- **Vendor Health Monitoring**: Track vendor reliability and response times
- **Plugin System**: Extensible architecture for custom scrapers and analyzers

## 📊 Data Sources

### Buylist Vendors
- **Star City Games** - Premium buylist prices
- **Card Kingdom** - Competitive buylist with store credit bonuses
- **BeatTheBuylist** - Aggregated buylist comparison
- **Channel Fireball** - Tournament-focused buylist
- **CoolStuffInc** - Gaming store buylist
- **CardShark** - Community-driven marketplace
- **Troll and Toad** - Established gaming retailer
- **Card Conduit** - Consignment and bulk pricing

### Market Data Sources
- **eBay Recent Sales** - Real market prices from completed auctions
- **TCG Player** - Market prices and buylist data
- **Cardmarket** - European market prices (EUR)
- **MTGGoldfish** - Price history and trends
- **MTGStocks** - Price spikes and movers
- **Scryfall** - Card metadata and price links
- **MagicCardPrices.io** - Market price aggregation
- **General Marketplaces** - Whatnot, Mercari, Facebook Marketplace, Amazon

## 🛠 Installation

```bash
# Clone the repository
git clone <repository-url>
cd MagicCardTrader

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## 📖 Usage

### Basic Commands

```bash
# Add cards to your collection
python -m mtg_buylist_aggregator.cli add-card "Sol Ring" "Commander 2021" 4

# Find best buylist prices
python -m mtg_buylist_aggregator.cli find-best-prices

# Get hot card recommendations
python -m mtg_buylist_aggregator.cli hot-cards

# View collection analytics
python -m mtg_buylist_aggregator.cli analytics
```

### Advanced Analysis

```bash
# Comprehensive market analysis with all data sources
python -m mtg_buylist_aggregator.cli --verbose market-analysis

# Research available vendors and pricing sources
python -m mtg_buylist_aggregator.cli research

# Check vendor health and reliability
python -m mtg_buylist_aggregator.cli vendor-health

# Get personalized recommendations
python -m mtg_buylist_aggregator.cli recommendations
```

### Testing and Development

```bash
# Use mock scrapers for testing
python -m mtg_buylist_aggregator.cli market-analysis --use-mock

# Export results to CSV
python -m mtg_buylist_aggregator.cli market-analysis --export-csv results.csv

# Run with custom configuration
python -m mtg_buylist_aggregator.cli --config custom_config.yaml find-best-prices
```

## 📈 Market Analysis Features

### Enhanced Price Analyzer
The enhanced price analyzer combines data from multiple sources to provide comprehensive market insights:

- **Multi-Source Aggregation**: Combines buylist, market, and sales data
- **Trend Detection**: Identifies price movements and volatility
- **Risk Assessment**: Evaluates investment risk based on price stability
- **Recommendation Engine**: Provides buy/sell/hold recommendations

### Price Sources Integration
- **Buylist Prices**: Direct from vendor websites
- **Market Prices**: Current selling prices from major marketplaces
- **Recent Sales**: Actual transaction data from eBay and other platforms
- **Price History**: Historical trends from MTGGoldfish and MTGStocks
- **Regional Markets**: European prices from Cardmarket

## 🔧 Configuration

### Global Settings
```yaml
# config.yaml
logging:
  level: INFO
  file: mtg_trader.log

scrapers:
  max_workers: 10
  timeout: 30
  retry_attempts: 3

analysis:
  hot_card_threshold: 0.15
  risk_threshold: 0.25
  trend_window_days: 30
```

### Vendor-Specific Settings
```yaml
vendors:
  star_city_games:
    enabled: true
    priority: 1
  card_kingdom:
    enabled: true
    priority: 2
  ebay:
    enabled: true
    priority: 3
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/test_analytics.py
python -m pytest tests/test_models.py

# Run with coverage
python -m pytest --cov=mtg_buylist_aggregator
```

## 📊 Output Examples

### Market Analysis Report
```
=== MARKET ANALYSIS REPORT ===
Analysis Date: 2025-06-21 19:43:58
Cards Analyzed: 10
Total Market Value: $152.55
Total Buylist Value: $149.26
Average Price Spread: $0.33
Average Volatility: $1.06
Average Risk Score: 0.11

=== RECOMMENDATIONS SUMMARY ===
HOLD: 10 cards
  - Sol Ring
  - Rhystic Study
  - Demonic Tutor
  ... and 7 more

=== DETAILED INSIGHTS ===
Card                      Market   Buylist  Spread   Trend    Risk   Rec         
-------------------------------------------------------------------------------------
Snapcaster Mage           $17.55   $16.49   $1.05    0%       0.04   HOLD        
Tarmogoyf                 $35.78   $35.02   $0.77    0%       0.26   HOLD        
Rhystic Study             $51.24   $50.50   $0.74    0%       0.36   HOLD        
```

### Vendor Health Report
```
=== VENDOR HEALTH REPORT ===
Total Vendors: 16
Healthy: 14
Degraded: 2
Failed: 0

VENDOR STATUS
=============
✅ Star City Games - Response: 0.8s, Success: 95%
✅ Card Kingdom - Response: 1.2s, Success: 92%
⚠️  eBay - Response: 3.1s, Success: 78%
✅ TCG Player - Response: 1.5s, Success: 88%
```

## 🔌 Plugin System

The system supports custom plugins for additional scrapers and analyzers:

```python
# plugins/custom_vendor.py
from mtg_buylist_aggregator.scrapers.base_scraper import BaseScraper

class CustomVendorScraper(BaseScraper):
    def __init__(self):
        super().__init__("Custom Vendor", "https://customvendor.com")
    
    def search_card(self, card):
        # Implement custom scraping logic
        pass
    
    def get_buylist(self):
        # Return complete buylist
        pass
```

## 📝 Data Models

### Card Model
```python
@dataclass
class Card:
    name: str
    set_name: str
    quantity: int
    condition: str = "Near Mint"
    foil: bool = False
    language: str = "English"
```

### Price Data Model
```python
@dataclass
class PriceData:
    vendor: str
    price: float
    condition: str
    quantity_limit: Optional[int]
    last_price_update: datetime
    all_conditions: Dict[str, Any]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information

## 🔮 Roadmap

- [ ] Real-time price alerts
- [ ] Mobile app interface
- [ ] Advanced portfolio tracking
- [ ] Integration with deck building tools
- [ ] Automated trading strategies
- [ ] Social features for card trading 