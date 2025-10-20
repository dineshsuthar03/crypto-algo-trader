from strategy.base_strategy import BaseStrategy
from core.logger import get_logger

logger = get_logger()

class PriceActionStrategy(BaseStrategy):
    """
    Simple price action strategy - generates signals on every candle
    Best for testing and high-frequency trading
    """
    
    def __init__(self):
        self.prev_close = None
        
    def generate_signal(self, candle):
        """
        Generate signal based on simple price action:
        - BUY: Close > Open AND increasing from previous close
        - SELL: Close < Open AND decreasing from previous close
        """
        current_open = candle['open']
        current_close = candle['close']
        current_high = candle['high']
        current_low = candle['low']
        
        if self.prev_close is None:
            self.prev_close = current_close
            return None
        
        signal = None
        
        # Calculate candle metrics
        body = abs(current_close - current_open)
        candle_range = current_high - current_low
        price_change = current_close - self.prev_close
        price_change_pct = (price_change / self.prev_close) * 100
        
        # Avoid division by zero
        if candle_range == 0:
            self.prev_close = current_close
            return None
        
        # Body to range ratio (strong candle if > 0.5)
        body_ratio = body / candle_range if candle_range > 0 else 0
        
        # BUY conditions:
        # 1. Close > Open (bullish candle)
        # 2. Price increased from previous close
        # 3. Decent body size (not a doji)
        if (current_close > current_open and 
            price_change > 0 and 
            body_ratio > 0.3 and
            abs(price_change_pct) > 0.01):  # At least 0.01% movement
            
            signal = "BUY"
            logger.debug(
                f"BUY signal: Close {current_close:.8f} > Open {current_open:.8f} | "
                f"Change: {price_change_pct:.4f}% | Body ratio: {body_ratio:.2f}"
            )
        
        # SELL conditions:
        # 1. Close < Open (bearish candle)
        # 2. Price decreased from previous close
        # 3. Decent body size (not a doji)
        elif (current_close < current_open and 
              price_change < 0 and 
              body_ratio > 0.3 and
              abs(price_change_pct) > 0.01):  # At least 0.01% movement
            
            signal = "SELL"
            logger.debug(
                f"SELL signal: Close {current_close:.8f} < Open {current_open:.8f} | "
                f"Change: {price_change_pct:.4f}% | Body ratio: {body_ratio:.2f}"
            )
        
        # Update previous close
        self.prev_close = current_close
        
        return signal