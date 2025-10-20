import numpy as np
from strategy.base_strategy import BaseStrategy

class CandlestickPatterns(BaseStrategy):
    """
    Strategy based on candlestick patterns
    Implements various Japanese candlestick patterns
    """
    
    def __init__(self):
        super().__init__()
        self.min_pattern_bars = 5
        self.confirmation_bars = 2
    
    def is_doji(self, open_price, high, low, close, doji_size=0.1):
        """Check if candle is a doji"""
        body_size = abs(close - open_price)
        total_range = high - low
        if total_range == 0:
            return False
        return body_size / total_range < doji_size
    
    def is_hammer(self, open_price, high, low, close):
        """
        Identify hammer pattern
        Long lower shadow, small body at the top
        """
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        
        if lower_shadow < body_size * 2:
            return False
        if upper_shadow > body_size:
            return False
        if body_size < (high - low) * 0.3:
            return True
        return False
    
    def is_engulfing(self, curr_open, curr_close, prev_open, prev_close):
        """Identify bullish/bearish engulfing patterns"""
        if curr_open > prev_close and curr_close < prev_open:
            return "BEARISH"
        elif curr_open < prev_close and curr_close > prev_open:
            return "BULLISH"
        return None
    
    def is_morning_star(self, opens, highs, lows, closes):
        """
        Identify morning star pattern (bullish reversal)
        Three candle pattern
        """
        if len(opens) < 3:
            return False
            
        # First candle: large bearish
        first_body = closes[-3] - opens[-3]
        if first_body >= 0:  # Must be bearish
            return False
            
        # Second candle: small body (doji-like)
        if not self.is_doji(opens[-2], highs[-2], lows[-2], closes[-2]):
            return False
            
        # Third candle: large bullish
        third_body = closes[-1] - opens[-1]
        if third_body <= 0:  # Must be bullish
            return False
            
        # Gap conditions
        if min(opens[-2], closes[-2]) > min(opens[-3], closes[-3]):
            return False
        if max(opens[-2], closes[-2]) < max(opens[-1], closes[-1]):
            return False
            
        return True
    
    def is_evening_star(self, opens, highs, lows, closes):
        """
        Identify evening star pattern (bearish reversal)
        Three candle pattern
        """
        if len(opens) < 3:
            return False
            
        # First candle: large bullish
        first_body = closes[-3] - opens[-3]
        if first_body <= 0:  # Must be bullish
            return False
            
        # Second candle: small body (doji-like)
        if not self.is_doji(opens[-2], highs[-2], lows[-2], closes[-2]):
            return False
            
        # Third candle: large bearish
        third_body = closes[-1] - opens[-1]
        if third_body >= 0:  # Must be bearish
            return False
            
        # Gap conditions
        if max(opens[-2], closes[-2]) < max(opens[-3], closes[-3]):
            return False
        if min(opens[-2], closes[-2]) > min(opens[-1], closes[-1]):
            return False
            
        return True
    
    def is_three_white_soldiers(self, opens, highs, lows, closes, threshold=0.1):
        """
        Identify three white soldiers pattern (bullish continuation)
        Three consecutive bullish candles with higher highs/lows
        """
        if len(opens) < 3:
            return False
            
        for i in range(-3, 0):
            # Must be bullish candles
            if closes[i] <= opens[i]:
                return False
            
            # Each candle should open within previous body
            if i > -3 and opens[i] < opens[i-1]:
                return False
            
            # Small upper shadows
            upper_shadow = highs[i] - closes[i]
            body_size = closes[i] - opens[i]
            if upper_shadow > body_size * threshold:
                return False
        
        return True
    
    def is_three_black_crows(self, opens, highs, lows, closes, threshold=0.1):
        """
        Identify three black crows pattern (bearish continuation)
        Three consecutive bearish candles with lower highs/lows
        """
        if len(opens) < 3:
            return False
            
        for i in range(-3, 0):
            # Must be bearish candles
            if closes[i] >= opens[i]:
                return False
            
            # Each candle should open within previous body
            if i > -3 and opens[i] > opens[i-1]:
                return False
            
            # Small lower shadows
            lower_shadow = closes[i] - lows[i]
            body_size = opens[i] - closes[i]
            if lower_shadow > body_size * threshold:
                return False
        
        return True

    def analyze(self, candles):
        """
        Analyze price action and identify patterns
        Returns: dict with pattern signals
        """
        if len(candles) < self.min_pattern_bars:
            return None
            
        opens = np.array([c['open'] for c in candles])
        highs = np.array([c['high'] for c in candles])
        lows = np.array([c['low'] for c in candles])
        closes = np.array([c['close'] for c in candles])
        
        signals = {
            'doji': False,
            'hammer': False,
            'engulfing': None,
            'morning_star': False,
            'evening_star': False,
            'three_white_soldiers': False,
            'three_black_crows': False
        }
        
        # Check latest candle for doji
        signals['doji'] = self.is_doji(opens[-1], highs[-1], lows[-1], closes[-1])
        
        # Check for hammer
        signals['hammer'] = self.is_hammer(opens[-1], highs[-1], lows[-1], closes[-1])
        
        # Check for engulfing
        if len(candles) >= 2:
            signals['engulfing'] = self.is_engulfing(
                opens[-1], closes[-1], opens[-2], closes[-2]
            )
        
        # Check for three candle patterns
        if len(candles) >= 3:
            signals['morning_star'] = self.is_morning_star(opens, highs, lows, closes)
            signals['evening_star'] = self.is_evening_star(opens, highs, lows, closes)
            signals['three_white_soldiers'] = self.is_three_white_soldiers(opens, highs, lows, closes)
            signals['three_black_crows'] = self.is_three_black_crows(opens, highs, lows, closes)
        
        return signals