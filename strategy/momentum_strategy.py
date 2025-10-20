from strategy.base_strategy import BaseStrategy
from collections import deque
from core.logger import get_logger

logger = get_logger()

class MomentumStrategy(BaseStrategy):
    """
    Momentum-based strategy - more sensitive for volatile coins like SHIB
    Tracks last N candles and generates signals based on price momentum
    """
    
    def __init__(self, lookback=3):
        self.lookback = lookback
        self.price_history = deque(maxlen=lookback)
        self.volume_history = deque(maxlen=lookback)
        
    def generate_signal(self, candle):
        """
        Generate signal based on momentum:
        - BUY: Price moving up with increasing volume
        - SELL: Price moving down with increasing volume
        """
        current_price = candle['close']
        current_volume = candle['volume']
        
        # Store current data
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)
        
        # Need enough history
        if len(self.price_history) < self.lookback:
            return None
        
        # Calculate momentum
        prices = list(self.price_history)
        volumes = list(self.volume_history)
        
        # Price momentum (% change from oldest to newest)
        price_change_pct = ((prices[-1] - prices[0]) / prices[0]) * 100
        
        # Volume trend (is volume increasing?)
        volume_increasing = volumes[-1] > sum(volumes[:-1]) / (len(volumes) - 1)
        
        # Recent price action (last vs second-to-last)
        recent_change = prices[-1] - prices[-2]
        
        signal = None
        
        # BUY: Upward momentum with volume
        if price_change_pct > 0.05 and volume_increasing and recent_change > 0:
            signal = "BUY"
            logger.debug(
                f"BUY signal: Price momentum {price_change_pct:.4f}% | "
                f"Current: {current_price:.8f} | Volume increasing: {volume_increasing}"
            )
        
        # SELL: Downward momentum with volume
        elif price_change_pct < -0.05 and volume_increasing and recent_change < 0:
            signal = "SELL"
            logger.debug(
                f"SELL signal: Price momentum {price_change_pct:.4f}% | "
                f"Current: {current_price:.8f} | Volume increasing: {volume_increasing}"
            )
        
        return signal