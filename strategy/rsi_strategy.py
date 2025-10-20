from strategy.base_strategy import BaseStrategy
from collections import deque
import numpy as np
from core.logger import get_logger

logger = get_logger()

class RSIStrategy(BaseStrategy):
    """
    RSI-based trading strategy
    - Uses Relative Strength Index (RSI) for overbought/oversold conditions
    - Combines RSI with volume and price action confirmation
    """
    
    def __init__(self, rsi_period=14, overbought=70, oversold=30):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.close_prices = deque(maxlen=rsi_period + 1)
        self.volumes = deque(maxlen=5)  # For volume confirmation
        self.last_rsi = None
        
    def calculate_rsi(self):
        """Calculate RSI using numpy for efficiency"""
        if len(self.close_prices) < self.rsi_period + 1:
            return None
            
        # Convert to numpy array for calculations
        prices = np.array(list(self.close_prices))
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = deltas.copy()
        losses = deltas.copy()
        
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = gains.mean()
        avg_loss = losses.mean()
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def is_volume_confirming(self, current_volume):
        """Check if volume is confirming the move"""
        if len(self.volumes) < 3:
            return False
            
        # Volume should be increasing
        vol_list = list(self.volumes)
        avg_volume = sum(vol_list[:-1]) / len(vol_list[:-1])
        return current_volume > avg_volume * 1.2  # 20% above average
        
    def generate_signal(self, candle):
        """
        Generate trading signals based on RSI with volume confirmation:
        - BUY: RSI moves from below oversold (30) back up + volume confirmation
        - SELL: RSI moves from above overbought (70) back down + volume confirmation
        """
        current_price = candle['close']
        current_volume = candle['volume']
        
        # Update price and volume history
        self.close_prices.append(current_price)
        self.volumes.append(current_volume)
        
        # Calculate current RSI
        current_rsi = self.calculate_rsi()
        
        if current_rsi is None or self.last_rsi is None:
            self.last_rsi = current_rsi
            return None
            
        signal = None
        
        # Volume confirmation
        volume_confirmed = self.is_volume_confirming(current_volume)
        
        # BUY Signal: RSI crosses up from oversold
        if (self.last_rsi <= self.oversold and 
            current_rsi > self.oversold and 
            volume_confirmed):
            signal = "BUY"
            logger.debug(
                f"BUY signal: RSI crossed up {self.oversold} | "
                f"Current RSI: {current_rsi:.2f} | "
                f"Price: {current_price:.8f} | "
                f"Volume confirmed: {volume_confirmed}"
            )
            
        # SELL Signal: RSI crosses down from overbought
        elif (self.last_rsi >= self.overbought and 
              current_rsi < self.overbought and 
              volume_confirmed):
            signal = "SELL"
            logger.debug(
                f"SELL signal: RSI crossed down {self.overbought} | "
                f"Current RSI: {current_rsi:.2f} | "
                f"Price: {current_price:.8f} | "
                f"Volume confirmed: {volume_confirmed}"
            )
            
        self.last_rsi = current_rsi
        return signal