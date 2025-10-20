import json
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from binance.client import Client
from strategy.candlestick_patterns import CandlestickPatterns
from strategy.chart_patterns import ChartPatterns
from strategy.combined_strategy import CombinedStrategy
from strategy.macd_strategy import MACDStrategy
from strategy.rsi_strategy import RSIStrategy
from strategy.momentum_strategy import MomentumStrategy
from core.config import BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET
from core.logger import get_logger

logger = get_logger()

class AdvancedStrategyTester:
    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)
        self.results_dir = "test_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize all strategies
        self.strategies = {
            'candlestick': CandlestickPatterns(),
            'chart': ChartPatterns(),
            'combined': CombinedStrategy(),
            'macd': MACDStrategy(),
            'rsi': RSIStrategy(),
            'momentum': MomentumStrategy()
        }
        
        # Test parameters for each strategy
        self.test_params = {
            'candlestick': {
                'doji_sizes': [0.1, 0.15, 0.2],
                'body_sizes': [0.3, 0.5, 0.7],
                'shadow_lengths': [1.5, 2.0, 2.5]
            },
            'chart': {
                'tolerances': [0.02, 0.03, 0.05],
                'min_swings': [3, 5, 7],
                'trend_strengths': [0.1, 0.15, 0.2]
            },
            'macd': {
                'fast_periods': [12, 8, 16],
                'slow_periods': [26, 21, 34],
                'signal_periods': [9, 7, 14]
            },
            'rsi': {
                'periods': [14, 21, 28],
                'overbought_levels': [70, 75, 80],
                'oversold_levels': [30, 25, 20]
            },
            'momentum': {
                'lookback_periods': [10, 20, 30],
                'threshold_multipliers': [1.5, 2.0, 2.5]
            }
        }
        
        # Timeframes to test
        self.timeframes = ['1h', '4h', '1d']
        
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
        
    def calculate_performance_metrics(self, signals, candles):
        """Calculate performance metrics for signals"""
        if not signals:
            return {}
            
        # Convert signals to DataFrame
        df_signals = pd.DataFrame(signals)
        
        # Convert candles to DataFrame
        df_candles = pd.DataFrame(candles)
        df_candles['timestamp'] = pd.to_datetime(df_candles['timestamp'], unit='ms')
        df_candles.set_index('timestamp', inplace=True)
        
        metrics = {
            'total_signals': len(signals),
            'signal_frequency': len(signals) / len(candles),
            'patterns': {},
            'win_rate': 0,
            'avg_profit': 0,
            'max_drawdown': 0,
            'profit_factor': 0
        }
        
        # Calculate pattern-specific metrics
        if 'pattern' in df_signals.columns:
            pattern_counts = df_signals['pattern'].value_counts().to_dict()
            metrics['patterns'] = pattern_counts
        
        return metrics
        
    def backtest_strategy(self, strategy_name, symbol, interval, params, lookback=30):
        """Backtest a strategy with specific parameters"""
        candles = self.get_historical_data(symbol, interval, lookback)
        if not candles:
            return None
            
        strategy = self.strategies[strategy_name]
        signals = []
        
        # Set strategy parameters
        for param, value in params.items():
            if hasattr(strategy, param):
                setattr(strategy, param, value)
        
        # Generate signals
        window_size = 50
        for i in range(window_size, len(candles)):
            window = candles[i-window_size:i+1]
            result = strategy.analyze(window)
            
            if result:
                timestamp = candles[i]['timestamp']
                price = candles[i]['close']
                
                if isinstance(result, dict):
                    for pattern, value in result.items():
                        if value:
                            signals.append({
                                'timestamp': timestamp,
                                'pattern': pattern,
                                'signal': value,
                                'price': price,
                                'params': params
                            })
                else:
                    signals.append({
                        'timestamp': timestamp,
                        'signal': result,
                        'price': price,
                        'params': params
                    })
        
        # Calculate performance metrics
        metrics = self.calculate_performance_metrics(signals, candles)
        
        return {
            'signals': signals,
            'metrics': metrics,
            'params': params
        }
    
    def test_all_strategies(self, symbol='BTCUSDT'):
        """Test all strategies with different parameters"""
        results = {}
        
        for strategy_name, strategy_params in self.test_params.items():
            logger.info(f"\nTesting {strategy_name} strategy...")
            strategy_results = {
                'timeframes': {},
                'best_params': {},
                'overall_metrics': {}
            }
            
            # Test each timeframe
            for interval in self.timeframes:
                timeframe_results = []
                param_combinations = self._generate_param_combinations(strategy_params)
                
                for params in param_combinations:
                    result = self.backtest_strategy(
                        strategy_name, symbol, interval, params
                    )
                    if result:
                        timeframe_results.append(result)
                
                # Find best parameters for this timeframe
                if timeframe_results:
                    best_result = max(
                        timeframe_results,
                        key=lambda x: x['metrics'].get('win_rate', 0)
                    )
                    strategy_results['timeframes'][interval] = best_result
            
            # Save results
            results[strategy_name] = strategy_results
            self._save_results(strategy_name, strategy_results)
            
            logger.info(f"Completed testing {strategy_name} strategy")
        
        return results
    
    def _generate_param_combinations(self, params_dict):
        """Generate all possible parameter combinations"""
        import itertools
        
        keys = params_dict.keys()
        values = params_dict.values()
        combinations = list(itertools.product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations]
    
    def _save_results(self, strategy_name, results):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.results_dir}/{strategy_name}_{timestamp}.json"
        
        # Convert datetime objects to string
        results_copy = self._prepare_results_for_json(results)
        
        with open(filename, 'w') as f:
            json.dump(results_copy, f, indent=4)
            
        logger.info(f"Results saved to {filename}")
    
    def _prepare_results_for_json(self, results):
        """Prepare results for JSON serialization"""
        if isinstance(results, dict):
            return {k: self._prepare_results_for_json(v) for k, v in results.items()}
        elif isinstance(results, list):
            return [self._prepare_results_for_json(item) for item in results]
        elif isinstance(results, (np.int64, np.float64)):
            return float(results)
        elif isinstance(results, np.bool_):
            return bool(results)
        elif isinstance(results, (datetime, pd.Timestamp)):
            return results.isoformat()
        return results

def main():
    tester = AdvancedStrategyTester()
    results = tester.test_all_strategies()
    
    # Print summary
    logger.info("\nTest Summary:")
    for strategy_name, strategy_results in results.items():
        logger.info(f"\n{strategy_name} Strategy:")
        for timeframe, result in strategy_results['timeframes'].items():
            metrics = result['metrics']
            logger.info(f"\nTimeframe: {timeframe}")
            logger.info(f"Total Signals: {metrics['total_signals']}")
            logger.info(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
            logger.info(f"Best Parameters: {result['params']}")
            
            if 'patterns' in metrics:
                logger.info("\nPattern Distribution:")
                for pattern, count in metrics['patterns'].items():
                    logger.info(f"{pattern}: {count}")

if __name__ == "__main__":
    main()