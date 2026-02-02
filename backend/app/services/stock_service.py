import os
from datetime import datetime

import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class StockService:
    """Service for fetching stock data from Alpha Vantage and yfinance"""

    @staticmethod
    def search_stocks(query: str) -> list[dict]:
        """Search for stocks using Yahoo Finance search API (consistent with yfinance data)"""
        try:
            # Use Yahoo Finance search API directly for consistency with yfinance
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                "q": query,
                "quotesCount": 10,
                "newsCount": 0,
                "listsCount": 0,
                "quotesQueryId": "tss_match_phrase_query"
            }
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for quote in data.get("quotes", []):
                # Filter to only equity types (stocks)
                if quote.get("quoteType") not in ["EQUITY", "ETF"]:
                    continue
                results.append({
                    "symbol": quote.get("symbol"),
                    "name": quote.get("longname") or quote.get("shortname"),
                    "type": quote.get("quoteType"),
                    "region": quote.get("exchange"),
                    "currency": quote.get("currency", "USD")
                })
            return results
        except Exception as e:
            print(f"Yahoo Finance search error: {e}")
            return []

    @staticmethod
    def get_stock_quote(symbol: str) -> dict | None:
        """Get real-time quote for a stock using yfinance (primary) and Alpha Vantage (backup)"""
        try:
            # Primary: yfinance (faster and no rate limits)
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                raise ValueError("Invalid symbol")

            # Get current price and calculate change
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

            change = None
            change_percent = None
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100

            return {
                "symbol": symbol.upper(),
                "name": info.get("longName") or info.get("shortName"),
                "price": current_price,
                "change": round(change, 2) if change else None,
                "change_percent": round(change_percent, 2) if change_percent else None,
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "previous_close": previous_close,
                "currency": info.get("currency", "USD"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"yfinance quote error: {e}")
            # Fallback to Alpha Vantage
            try:
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": ALPHA_VANTAGE_API_KEY
                }
                response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("Global Quote"):
                    quote = data["Global Quote"]
                    return {
                        "symbol": quote.get("01. symbol"),
                        "name": symbol,
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": float(quote.get("10. change percent", "0").replace("%", "")),
                        "volume": int(quote.get("06. volume", 0)),
                        "market_cap": None,
                        "day_high": float(quote.get("03. high", 0)),
                        "day_low": float(quote.get("04. low", 0)),
                        "open": float(quote.get("02. open", 0)),
                        "previous_close": float(quote.get("08. previous close", 0)),
                        "currency": "USD",
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as av_error:
                print(f"Alpha Vantage quote error: {av_error}")

            return None

    @staticmethod
    def get_stock_history(symbol: str, period: str = "1M") -> dict | None:
        """Get historical price data using yfinance"""
        try:
            # Map period to yfinance period format
            period_map = {
                "1D": "1d",
                "1W": "5d",
                "1M": "1mo",
                "3M": "3mo",
                "6M": "6mo",
                "1Y": "1y",
                "5Y": "5y"
            }

            yf_period = period_map.get(period, "1mo")
            print(f"Fetching history for {symbol} with period {yf_period}")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=yf_period)

            print(f"History data shape: {hist.shape}")
            print(f"History empty: {hist.empty}")

            if hist.empty:
                print(f"No historical data found for {symbol}")
                return None

            # Convert DataFrame to list of dicts
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"])
                })

            print(f"Returning {len(history_data)} history records")
            return {
                "symbol": symbol.upper(),
                "period": period,
                "data": history_data
            }
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_company_info(symbol: str) -> dict | None:
        """Get company information and fundamentals using yfinance"""
        try:
            print(f"Fetching company info for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info

            print(f"Info keys: {list(info.keys())[:10] if info else 'None'}")
            print(f"Symbol in info: {'symbol' in info if info else False}")

            if not info or "symbol" not in info:
                print(f"No valid company info found for {symbol}")
                return None

            result = {
                "symbol": symbol.upper(),
                "name": info.get("longName") or info.get("shortName"),
                "description": info.get("longBusinessSummary"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "currency": info.get("currency", "USD")
            }
            print(f"Returning company info with name: {result['name']}")
            return result
        except Exception as e:
            print(f"Error fetching company info for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None


# Create a singleton instance
stock_service = StockService()
