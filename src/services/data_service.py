"""
Financial Data Service
Integrates Alpha Vantage, QuickSight, and real-time market data
"""

import asyncio
import aiohttp
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import json

class AlphaVantageService:
    """Alpha Vantage API integration for financial data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
    async def get_stock_data(self, symbol: str, interval: str = "1min") -> Dict:
        """Get real-time stock data"""
        
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
            "outputsize": "compact"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                return self._process_stock_data(data)
    
    async def get_company_overview(self, symbol: str) -> Dict:
        """Get company fundamental data"""
        
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                return await response.json()
    
    async def get_financial_statements(self, symbol: str) -> Dict:
        """Get income statement, balance sheet, cash flow"""
        
        statements = {}
        functions = ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]
        
        async with aiohttp.ClientSession() as session:
            for function in functions:
                params = {
                    "function": function,
                    "symbol": symbol,
                    "apikey": self.api_key
                }
                async with session.get(self.base_url, params=params) as response:
                    statements[function.lower()] = await response.json()
        
        return statements
    
    def _process_stock_data(self, raw_data: Dict) -> Dict:
        """Process and clean stock data"""
        
        if "Time Series (1min)" in raw_data:
            time_series = raw_data["Time Series (1min)"]
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            
            # Calculate technical indicators
            df['sma_20'] = df['4. close'].rolling(window=20).mean()
            df['rsi'] = self._calculate_rsi(df['4. close'])
            
            return {
                "symbol": raw_data.get("Meta Data", {}).get("2. Symbol"),
                "last_refreshed": raw_data.get("Meta Data", {}).get("3. Last Refreshed"),
                "current_price": float(df.iloc[0]['4. close']),
                "change": float(df.iloc[0]['4. close']) - float(df.iloc[1]['4. close']),
                "volume": int(df.iloc[0]['5. volume']),
                "technical_indicators": {
                    "sma_20": df.iloc[0]['sma_20'],
                    "rsi": df.iloc[0]['rsi']
                },
                "time_series": df.head(100).to_dict('records')
            }
        
        return raw_data
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI technical indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

class QuickSightService:
    """Amazon QuickSight integration for dashboards"""
    
    def __init__(self, region: str = "us-east-1"):
        self.quicksight = boto3.client('quicksight', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
    
    async def create_financial_dashboard(self, 
                                       dashboard_name: str,
                                       data_source_arn: str) -> Dict:
        """Create a financial analytics dashboard"""
        
        try:
            response = self.quicksight.create_dashboard(
                AwsAccountId=self.account_id,
                DashboardId=f"financial-{dashboard_name}",
                Name=f"Financial Analytics - {dashboard_name}",
                Definition={
                    'DataSetIdentifierDeclarations': [
                        {
                            'DataSetArn': data_source_arn,
                            'Identifier': 'financial_data'
                        }
                    ],
                    'Sheets': [
                        {
                            'SheetId': 'sheet1',
                            'Name': 'Market Overview',
                            'Visuals': self._create_financial_visuals()
                        }
                    ]
                }
            )
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def _create_financial_visuals(self) -> List[Dict]:
        """Create financial visualization configurations"""
        
        return [
            {
                'LineChartVisual': {
                    'VisualId': 'price-chart',
                    'Title': {'Visibility': 'VISIBLE', 'Label': 'Price Movement'},
                    'ChartConfiguration': {
                        'FieldWells': {
                            'LineChartAggregatedFieldWells': {
                                'Category': [{'DateDimensionField': {'FieldId': 'date'}}],
                                'Values': [{'NumericalMeasureField': {'FieldId': 'price'}}]
                            }
                        }
                    }
                }
            }
        ]

class RealTimeDataService:
    """Real-time market data processing"""
    
    def __init__(self):
        self.alpha_vantage = None
        self.quicksight = None
        self.cache = {}
        
    def initialize(self, alpha_vantage_key: str):
        """Initialize data services"""
        self.alpha_vantage = AlphaVantageService(alpha_vantage_key)
        self.quicksight = QuickSightService()
    
    async def get_market_snapshot(self, symbols: List[str]) -> Dict:
        """Get real-time market snapshot for multiple symbols"""
        
        tasks = []
        for symbol in symbols:
            tasks.append(self.alpha_vantage.get_stock_data(symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        market_data = {}
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                market_data[symbols[i]] = result
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "market_data": market_data,
            "market_summary": self._calculate_market_summary(market_data)
        }
    
    def _calculate_market_summary(self, market_data: Dict) -> Dict:
        """Calculate overall market summary statistics"""
        
        if not market_data:
            return {}
        
        prices = [data.get("current_price", 0) for data in market_data.values()]
        changes = [data.get("change", 0) for data in market_data.values()]
        
        return {
            "total_symbols": len(market_data),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "total_change": sum(changes),
            "gainers": len([c for c in changes if c > 0]),
            "losers": len([c for c in changes if c < 0])
        }