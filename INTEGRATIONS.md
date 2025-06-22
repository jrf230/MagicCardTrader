# MTG Buylist Aggregator - Integrations Guide

This document provides detailed information about all data sources and integrations in the MTG Buylist Aggregator.

## 📊 Data Sources Overview

The system integrates with **16 different data sources** across multiple categories:

### Buylist Vendors (8 sources)
- Traditional buylist prices from established MTG retailers
- Focus on selling cards to vendors

### Market Data Sources (8 sources)
- Current market prices and sales data
- Price history and trend analysis
- Regional market data

## 🏪 Buylist Vendors

### 1. Star City Games
- **URL**: https://starcitygames.com
- **Focus**: Premium buylist prices, tournament support
- **Strengths**: High prices for competitive cards, store credit bonuses
- **Limitations**: Strict condition requirements
- **Best For**: High-value competitive cards

### 2. Card Kingdom
- **URL**: https://cardkingdom.com
- **Focus**: Competitive buylist with store credit bonuses
- **Strengths**: Good prices, excellent store credit rates
- **Limitations**: May have lower cash prices
- **Best For**: Players who want store credit

### 3. BeatTheBuylist
- **URL**: https://beatthebuylist.com
- **Focus**: Aggregated buylist comparison
- **Strengths**: Compares multiple vendors automatically
- **Limitations**: May not always have the best individual prices
- **Best For**: Quick comparison shopping

### 4. Channel Fireball
- **URL**: https://store.channelfireball.com
- **Focus**: Tournament-focused buylist
- **Strengths**: Good prices for tournament staples
- **Limitations**: Limited selection of casual cards
- **Best For**: Tournament players

### 5. CoolStuffInc
- **URL**: https://www.coolstuffinc.com
- **Focus**: Gaming store buylist
- **Strengths**: Competitive prices, good customer service
- **Limitations**: May have quantity limits
- **Best For**: Local gaming community members

### 6. CardShark
- **URL**: https://www.cardshark.com
- **Focus**: Community-driven marketplace
- **Strengths**: Direct peer-to-peer trading
- **Limitations**: Variable pricing, requires negotiation
- **Best For**: Experienced traders

### 7. Troll and Toad
- **URL**: https://www.trollandtoad.com
- **Focus**: Established gaming retailer
- **Strengths**: Long history, reliable service
- **Limitations**: May not always have competitive prices
- **Best For**: Traditional retail experience

### 8. Card Conduit
- **URL**: https://www.cardconduit.com
- **Focus**: Consignment and bulk pricing
- **Strengths**: Handles large collections, professional service
- **Limitations**: May have minimum thresholds
- **Best For**: Large collection sales

## 📈 Market Data Sources

### 9. eBay Recent Sales
- **URL**: https://www.ebay.com
- **Focus**: Real market prices from completed auctions
- **Data Type**: Recent sales data, auction results
- **Strengths**: Real market prices, large volume of data
- **Limitations**: May include shipping costs, variable conditions
- **Best For**: Understanding true market value

### 10. TCG Player
- **URL**: https://www.tcgplayer.com
- **Focus**: Market prices and buylist data
- **Data Type**: Current selling prices, buylist prices
- **Strengths**: Large marketplace, comprehensive data
- **Limitations**: May have fees, variable seller quality
- **Best For**: Market price reference

### 11. Cardmarket
- **URL**: https://www.cardmarket.com
- **Focus**: European market prices (EUR)
- **Data Type**: European market data, regional pricing
- **Strengths**: European market insight, different price dynamics
- **Limitations**: EUR pricing, may not reflect US market
- **Best For**: European market analysis

### 12. MTGGoldfish
- **URL**: https://www.mtggoldfish.com
- **Focus**: Price history and trends
- **Data Type**: Historical price data, trend analysis
- **Strengths**: Excellent price history, trend identification
- **Limitations**: May not reflect current market conditions
- **Best For**: Long-term price analysis

### 13. MTGStocks
- **URL**: https://www.mtgstocks.com
- **Focus**: Price spikes and movers
- **Data Type**: Price movement alerts, volatility data
- **Strengths**: Identifies hot cards, price spikes
- **Limitations**: May be reactive rather than predictive
- **Best For**: Identifying trending cards

### 14. Scryfall
- **URL**: https://api.scryfall.com
- **Focus**: Card metadata and price links
- **Data Type**: Card information, price aggregation links
- **Strengths**: Comprehensive card database, API access
- **Limitations**: No direct pricing, links to other sources
- **Best For**: Card identification and metadata

### 15. MagicCardPrices.io
- **URL**: https://magiccardprices.io
- **Focus**: Market price aggregation
- **Data Type**: Aggregated price data from multiple sources
- **Strengths**: Multiple source aggregation, comprehensive coverage
- **Limitations**: May have delays, dependent on other sources
- **Best For**: Comprehensive price overview

### 16. General Marketplaces
- **Sources**: Whatnot, Mercari, Facebook Marketplace, Amazon
- **Focus**: Alternative sales channels
- **Data Type**: Sales data from various platforms
- **Strengths**: Diverse market coverage, alternative pricing
- **Limitations**: Variable data quality, may include fees
- **Best For**: Alternative market analysis

## 🔧 Integration Architecture

### Scraper Base Class
All scrapers inherit from `BaseScraper` and implement:
- `search_card(card)`: Search for a specific card
- `get_buylist()`: Get complete buylist (if applicable)

### Scraper Manager
The `ScraperManager` coordinates all scrapers:
- Parallel execution for performance
- Error handling and retry logic
- Vendor health monitoring
- Mock mode for testing

### Enhanced Price Analyzer
The `EnhancedPriceAnalyzer` combines data from multiple sources:
- Multi-source price aggregation
- Trend detection and analysis
- Risk assessment
- Recommendation generation

## 📊 Data Flow

```
Collection → ScraperManager → Multiple Sources → EnhancedAnalyzer → Recommendations
     ↓              ↓                ↓                ↓                ↓
   Cards      Parallel Scraping   Price Data    Market Analysis   Buy/Sell/Hold
```

## 🎯 Use Cases by Data Source

### For Buylist Optimization
**Primary Sources**: Star City Games, Card Kingdom, BeatTheBuylist
**Secondary Sources**: Channel Fireball, CoolStuffInc
**Use Case**: Find the best vendor to sell specific cards

### For Market Analysis
**Primary Sources**: TCG Player, eBay Recent Sales, MTGGoldfish
**Secondary Sources**: Cardmarket, MTGStocks
**Use Case**: Understand current market conditions and trends

### For Investment Decisions
**Primary Sources**: MTGGoldfish, MTGStocks, eBay Recent Sales
**Secondary Sources**: TCG Player, Cardmarket
**Use Case**: Identify cards with growth potential

### For Collection Valuation
**Primary Sources**: TCG Player, Cardmarket, eBay Recent Sales
**Secondary Sources**: MTGGoldfish, MagicCardPrices.io
**Use Case**: Accurate collection value assessment

## ⚙️ Configuration Options

### Vendor Priority
```yaml
vendors:
  star_city_games:
    priority: 1  # Highest priority
    enabled: true
  card_kingdom:
    priority: 2
    enabled: true
  ebay:
    priority: 3
    enabled: true
```

### Data Source Categories
```yaml
data_sources:
  buylist:
    - star_city_games
    - card_kingdom
    - beatthebuylist
  market:
    - tcg_player
    - ebay
    - cardmarket
  trends:
    - mtggoldfish
    - mtgstocks
```

### Performance Settings
```yaml
scrapers:
  max_workers: 10
  timeout: 30
  retry_attempts: 3
  rate_limit: 1.0  # seconds between requests
```

## 🔍 Monitoring and Health

### Vendor Health Metrics
- **Response Time**: How quickly vendors respond
- **Success Rate**: Percentage of successful requests
- **Data Quality**: Completeness and accuracy of data
- **Availability**: Uptime and reliability

### Health Status Levels
- **✅ Healthy**: < 2s response, > 90% success rate
- **⚠️ Degraded**: 2-5s response, 70-90% success rate
- **❌ Failed**: > 5s response, < 70% success rate

## 🚀 Future Integrations

### Planned Additions
- **TCGPlayer API**: Direct API access for better data
- **Cardmarket API**: European market API integration
- **MTGPrice**: Additional price aggregation
- **Deckbox**: Collection management integration
- **Moxfield**: Deck building tool integration

### Potential Sources
- **Facebook Groups**: Local trading groups
- **Discord Servers**: Community trading channels
- **Reddit**: r/mtgfinance and trading subreddits
- **Local Game Stores**: Regional pricing data

## 📝 Best Practices

### For Developers
1. **Respect Rate Limits**: Implement delays between requests
2. **Handle Errors Gracefully**: Don't fail completely if one source is down
3. **Cache Results**: Store data to reduce API calls
4. **Validate Data**: Ensure data quality and consistency

### For Users
1. **Use Multiple Sources**: Don't rely on a single vendor
2. **Consider Timing**: Prices can vary throughout the day
3. **Check Conditions**: Ensure condition requirements match
4. **Monitor Trends**: Use trend data for timing decisions

## 🔒 Legal and Ethical Considerations

### Terms of Service
- Respect each website's terms of service
- Implement appropriate rate limiting
- Don't overload servers with requests
- Use data responsibly and ethically

### Data Usage
- Use data for personal analysis only
- Don't redistribute data without permission
- Respect intellectual property rights
- Follow fair use guidelines

## 📞 Support and Troubleshooting

### Common Issues
1. **Vendor Unavailable**: Check vendor health status
2. **Data Inconsistencies**: Verify with multiple sources
3. **Rate Limiting**: Reduce request frequency
4. **Network Issues**: Check internet connectivity

### Getting Help
- Check vendor health reports
- Review error logs
- Test with mock data
- Contact support with detailed information 