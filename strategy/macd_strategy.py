import numpy as np
from strategy.base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.signal_distance = 0.0002  # Minimum distance between MACD and signal for valid cross
        self.last_macd = None
        self.last_signal = None
        
    def calculate_ema(self, data, period):
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = [data[0]]  # First value is simple average
        
        for price in data[1:]:
            ema.append(price * alpha + ema[-1] * (1 - alpha))
            
        return ema[-1]
        
    def calculate_macd(self):
        """Calculate MACD and Signal line"""
        if len(self.prices) < self.slow_period:
            return None, None
            
        prices = list(self.prices)
        
        # Calculate EMAs
        fast_ema = self.calculate_ema(prices, self.fast_period)
        slow_ema = self.calculate_ema(prices, self.slow_period)
        
        if fast_ema is None or slow_ema is None:
            return None, None
            
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate Signal line (EMA of MACD)
        macd_values = [macd_line] * self.signal_period  # Simplified for initial calculation
        signal_line = self.calculate_ema(macd_values, self.signal_period)
        
        return macd_line, signal_line
        
    def calculate_macd(self, closes):
        """Calculate MACD and Signal lines"""
        # Calculate EMAs
        fast_ema = self._calculate_ema(closes, self.fast_period)
        slow_ema = self._calculate_ema(closes, self.slow_period)
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate Signal line
        signal_line = self._calculate_ema(macd_line, self.signal_period)
        
        return macd_line, signal_line
    
    def _calculate_ema(self, data, period):
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return np.array([])
            
        multiplier = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[period-1] = np.mean(data[:period])  # First EMA is SMA
        
        for i in range(period, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
            
        return ema
    
    def detect_crossover(self, macd_line, signal_line):
        """Detect MACD line crossing Signal line"""
        if len(macd_line) < 2 or len(signal_line) < 2:
            return None
            
        # Check last two points
        prev_diff = macd_line[-2] - signal_line[-2]
        curr_diff = macd_line[-1] - signal_line[-1]
        
        # Check if difference is significant enough
        if abs(curr_diff) < self.signal_distance:
            return None
        
        # Bullish crossover
        if prev_diff < 0 and curr_diff > 0:
            return "BULLISH"
        # Bearish crossover
        elif prev_diff > 0 and curr_diff < 0:
            return "BEARISH"
            
        return None

    def check_histogram_divergence(self, closes, macd_line):
        """Check for price/MACD divergence"""
        if len(closes) < 10 or len(macd_line) < 10:
            return None
            
        # Get last 10 points for analysis
        price_window = closes[-10:]
        macd_window = macd_line[-10:]
        
        # Calculate price trend
        price_trend = 1 if price_window[-1] > price_window[0] else -1
        
        # Calculate MACD trend
        macd_trend = 1 if macd_window[-1] > macd_window[0] else -1
        
        # Check for divergence
        if price_trend != macd_trend:
            if price_trend > 0 and macd_trend < 0:
                return "BEARISH"  # Bearish divergence
            else:
                return "BULLISH"  # Bullish divergence
                
        return None
    
    def analyze(self, candles):
        """
        Analyze price data using MACD
        Returns: "BULLISH", "BEARISH", or None
        """
        if len(candles) < self.slow_period + self.signal_period:
            return None
            
        # Get closing prices
        closes = np.array([c['close'] for c in candles])
        
        # Calculate MACD indicators
        macd_line, signal_line = self.calculate_macd(closes)
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return None
            
        # Check for crossover signals
        crossover = self.detect_crossover(macd_line, signal_line)
        if crossover:
            return crossover
            
        # Check for divergence if no crossover
        divergence = self.check_histogram_divergence(closes, macd_line)
        if divergence:
            return divergence
            
        return None