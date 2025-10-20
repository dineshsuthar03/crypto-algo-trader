from strategy.breakout_strategy import BreakoutStrategy
from strategy.momentum_strategy import MomentumStrategy
from strategy.price_action_strategy import PriceActionStrategy
from strategy.rsi_strategy import RSIStrategy
from data_feed import candle_store
from core.config import SYMBOLS
from core.logger import get_logger

logger = get_logger()

import redis
from core.config import REDIS_HOST, REDIS_PORT

class StrategyEngine:
    """
    Strategy Engine - manages multiple strategies
    
    Available strategies:
    1. BreakoutStrategy - Trades breakouts above/below previous high/low
    2. MomentumStrategy - Trades based on price momentum and volume
    3. PriceActionStrategy - Simple candle-by-candle price action (most sensitive)
    """
    
    def __init__(self, strategy_type="price_action"):
        """
        Initialize strategy engine
        
        Args:
            strategy_type: "breakout", "momentum", or "price_action"
        """
        self.strategy_type = strategy_type
        self.strategies = {}
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        
        # Initialize strategies for each symbol
        for sym in SYMBOLS:
            if strategy_type == "breakout":
                self.strategies[sym] = [BreakoutStrategy()]
                logger.info(f"Loaded BreakoutStrategy for {sym}")
            elif strategy_type == "momentum":
                self.strategies[sym] = [MomentumStrategy(lookback=3)]
                logger.info(f"Loaded MomentumStrategy for {sym}")
            elif strategy_type == "price_action":
                self.strategies[sym] = [PriceActionStrategy()]
                logger.info(f"Loaded PriceActionStrategy for {sym}")
            elif strategy_type == "rsi":
                self.strategies[sym] = [RSIStrategy()]
                logger.info(f"Loaded RSIStrategy for {sym}")
            else:
                # Default to price action
                self.strategies[sym] = [PriceActionStrategy()]
                logger.warning(f"Unknown strategy type '{strategy_type}', using PriceActionStrategy")
    
    def run(self):
        """
        Run all strategies and collect signals. Also stores signals in Redis for position tracking.
        
        Returns:
            dict: {(symbol, strategy_name): signal}
        """
        signals = {}
        
        for sym in SYMBOLS:
            candle = candle_store.get_last_candle(sym)
            
            if not candle:
                continue
            
            # Run each strategy for this symbol
            for strat in self.strategies[sym]:
                try:
                    signal = strat.generate_signal(candle)
                    
                    # Only store non-None signals
                    if signal:
                        signals[(sym, type(strat).__name__)] = signal
                        
                except Exception as e:
                    logger.error(f"Error running {type(strat).__name__} for {sym}: {str(e)}")
        
        return signals
    
    def get_strategy_info(self):
        """Get information about loaded strategies"""
        info = {
            "strategy_type": self.strategy_type,
            "symbols": list(self.strategies.keys()),
            "strategies": {}
        }
        
        for sym, strats in self.strategies.items():
            info["strategies"][sym] = [type(s).__name__ for s in strats]
        
        return info