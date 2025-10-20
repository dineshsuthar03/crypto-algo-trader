import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import numpy as np
from binance.client import Client
from core.config import BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET
from strategy.candlestick_patterns import CandlestickPatterns
from strategy.chart_patterns import ChartPatterns
from strategy.combined_strategy import CombinedStrategy
from core.logger import get_logger

logger = get_logger()

class StrategyTester:
    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)
        self.strategies = {
            'candlestick': CandlestickPatterns(),
            'chart': ChartPatterns(),
            'combined': CombinedStrategy()
        }
        
    def get_historical_data(self, symbol, interval, lookback):
        """Get historical candlestick data"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback)
        
        klines = self.client.get_historical_klines(
            symbol,
            interval,
            start_str=start_time.strftime('%Y-%m-%d'),
            end_str=end_time.strftime('%Y-%m-%d')
        )
        
        candles = []
        for k in klines:
            candles.append({
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
            })
        
        return candles
        
    def test_strategy(self, strategy_name, symbol='BTCUSDT', interval='1h', lookback=30):
        """Test a specific strategy with historical data"""
        logger.info(f"Testing {strategy_name} strategy on {symbol} {interval} timeframe")
        
        # Get historical data
        candles = self.get_historical_data(symbol, interval, lookback)
        if not candles:
            logger.error("No historical data available")
            return
            
        # Get strategy instance
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            logger.error(f"Strategy {strategy_name} not found")
            return
            
        # Track signals and performance
        signals = []
        pattern_hits = {}
        
        # Analyze each candlestick
        window_size = 50  # Minimum candles needed for analysis
        for i in range(window_size, len(candles)):
            window = candles[i-window_size:i+1]
            result = strategy.analyze(window)
            
            if result:
                if isinstance(result, dict):
                    # For pattern-based strategies
                    for pattern, value in result.items():
                        if value:
                            pattern_hits[pattern] = pattern_hits.get(pattern, 0) + 1
                            signals.append({
                                'timestamp': candles[i]['timestamp'],
                                'pattern': pattern,
                                'signal': value,
                                'price': candles[i]['close']
                            })
                else:
                    # For simple signal strategies
                    signals.append({
                        'timestamp': candles[i]['timestamp'],
                        'signal': result,
                        'price': candles[i]['close']
                    })
        
        # Print results
        logger.info(f"\nTest Results for {strategy_name}:")
        logger.info(f"Total candles analyzed: {len(candles) - window_size}")
        logger.info(f"Total signals generated: {len(signals)}")
        
        if pattern_hits:
            logger.info("\nPattern Distribution:")
            for pattern, count in pattern_hits.items():
                logger.info(f"{pattern}: {count} occurrences")
        
        if signals:
            logger.info("\nLast 5 Signals:")
            for signal in signals[-5:]:
                timestamp = datetime.fromtimestamp(signal['timestamp']/1000)
                if 'pattern' in signal:
                    logger.info(f"{timestamp}: {signal['pattern']} - {signal['signal']} at {signal['price']}")
                else:
                    logger.info(f"{timestamp}: {signal['signal']} at {signal['price']}")
        
        return signals

def main():
    tester = StrategyTester()
    
    # Test parameters
    symbol = 'BTCUSDT'
    interval = '1h'
    lookback = 30  # days
    
    # Test each strategy
    strategies = ['candlestick', 'chart', 'combined']
    
    for strategy in strategies:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {strategy} strategy")
        logger.info(f"{'='*50}")
        
        signals = tester.test_strategy(strategy, symbol, interval, lookback)
        
        logger.info(f"\nCompleted testing {strategy} strategy")
        logger.info(f"{'='*50}\n")

if __name__ == "__main__":
    main()