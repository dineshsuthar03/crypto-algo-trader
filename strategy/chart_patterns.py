import numpy as np
from strategy.base_strategy import BaseStrategy

class ChartPatterns(BaseStrategy):
    """
    Strategy based on technical chart patterns
    Implements various chart patterns like triangles, flags, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.min_pattern_bars = 10
        self.tolerance = 0.02  # 2% tolerance for pattern matching
    
    def find_swing_points(self, prices, window=5):
        """Identify swing high and low points"""
        highs = []
        lows = []
        
        for i in range(window, len(prices) - window):
            left_window = prices[i-window:i]
            right_window = prices[i+1:i+window+1]
            current = prices[i]
            
            # Check for swing high
            if current > max(left_window) and current > max(right_window):
                highs.append((i, current))
            
            # Check for swing low
            if current < min(left_window) and current < min(right_window):
                lows.append((i, current))
                
        return highs, lows
    
    def is_ascending_triangle(self, prices, highs, lows, tolerance=0.02):
        """
        Identify ascending triangle pattern
        Flat top resistance line and rising support line
        """
        if len(highs) < 2 or len(lows) < 2:
            return False
            
        # Check for flat resistance
        high_points = [h[1] for h in highs[-3:]]
        high_mean = np.mean(high_points)
        if any(abs(h - high_mean) / high_mean > tolerance for h in high_points):
            return False
        
        # Check for rising support
        low_points = [l[1] for l in lows[-3:]]
        if not all(low_points[i] > low_points[i-1] for i in range(1, len(low_points))):
            return False
            
        return True
    
    def is_descending_triangle(self, prices, highs, lows, tolerance=0.02):
        """
        Identify descending triangle pattern
        Flat bottom support line and falling resistance line
        """
        if len(highs) < 2 or len(lows) < 2:
            return False
            
        # Check for flat support
        low_points = [l[1] for l in lows[-3:]]
        low_mean = np.mean(low_points)
        if any(abs(l - low_mean) / low_mean > tolerance for l in low_points):
            return False
        
        # Check for falling resistance
        high_points = [h[1] for h in highs[-3:]]
        if not all(high_points[i] < high_points[i-1] for i in range(1, len(high_points))):
            return False
            
        return True
    
    def is_flag_pattern(self, prices, direction="bullish", min_trend=10):
        """
        Identify flag pattern
        Parallel channel against the trend
        """
        if len(prices) < min_trend:
            return False
            
        # Check prior trend
        trend_section = prices[-min_trend:-min_trend//2]
        flag_section = prices[-min_trend//2:]
        
        if direction == "bullish":
            # Check for prior uptrend
            if not all(trend_section[i] > trend_section[i-1] for i in range(1, len(trend_section))):
                return False
            
            # Check for temporary pullback
            regression = np.polyfit(range(len(flag_section)), flag_section, 1)
            slope = regression[0]
            
            return slope < 0  # Negative slope for pullback
            
        else:  # bearish
            # Check for prior downtrend
            if not all(trend_section[i] < trend_section[i-1] for i in range(1, len(trend_section))):
                return False
            
            # Check for temporary bounce
            regression = np.polyfit(range(len(flag_section)), flag_section, 1)
            slope = regression[0]
            
            return slope > 0  # Positive slope for bounce
    
    def is_wedge_pattern(self, prices, highs, lows):
        """
        Identify rising/falling wedge patterns
        Converging trend lines with same direction
        """
        if len(highs) < 3 or len(lows) < 3:
            return False
            
        high_points = [h[1] for h in highs[-3:]]
        low_points = [l[1] for l in lows[-3:]]
        
        # Calculate slopes
        high_slope = np.polyfit(range(len(high_points)), high_points, 1)[0]
        low_slope = np.polyfit(range(len(low_points)), low_points, 1)[0]
        
        # Check for converging lines
        if abs(high_slope - low_slope) < self.tolerance:
            return False
            
        if high_slope > 0 and low_slope > 0:
            return "rising"
        elif high_slope < 0 and low_slope < 0:
            return "falling"
            
        return None
    
    def is_double_top(self, prices, highs, tolerance=0.02):
        """
        Identify double top pattern
        Two equal highs with a trough between
        """
        if len(highs) < 2:
            return False
            
        recent_highs = [h[1] for h in highs[-2:]]
        high_diff = abs(recent_highs[0] - recent_highs[1])
        
        # Check if highs are at similar levels
        if high_diff / recent_highs[0] > tolerance:
            return False
            
        # Check for significant trough between highs
        between_index = range(highs[-2][0], highs[-1][0])
        between_prices = [prices[i] for i in between_index]
        
        if not between_prices:
            return False
            
        trough = min(between_prices)
        trough_depth = recent_highs[0] - trough
        
        return trough_depth / recent_highs[0] > 0.05  # At least 5% depth
    
    def is_double_bottom(self, prices, lows, tolerance=0.02):
        """
        Identify double bottom pattern
        Two equal lows with a peak between
        """
        if len(lows) < 2:
            return False
            
        recent_lows = [l[1] for l in lows[-2:]]
        low_diff = abs(recent_lows[0] - recent_lows[1])
        
        # Check if lows are at similar levels
        if low_diff / recent_lows[0] > tolerance:
            return False
            
        # Check for significant peak between lows
        between_index = range(lows[-2][0], lows[-1][0])
        between_prices = [prices[i] for i in between_index]
        
        if not between_prices:
            return False
            
        peak = max(between_prices)
        peak_height = peak - recent_lows[0]
        
        return peak_height / recent_lows[0] > 0.05  # At least 5% height
        
    def analyze(self, candles):
        """
        Analyze price action and identify chart patterns
        Returns: dict with pattern signals
        """
        if len(candles) < self.min_pattern_bars:
            return None
            
        closes = np.array([c['close'] for c in candles])
        highs_data = np.array([c['high'] for c in candles])
        lows_data = np.array([c['low'] for c in candles])
        
        # Find swing points
        swing_highs, swing_lows = self.find_swing_points(closes)
        
        signals = {
            'ascending_triangle': False,
            'descending_triangle': False,
            'bullish_flag': False,
            'bearish_flag': False,
            'wedge': None,
            'double_top': False,
            'double_bottom': False
        }
        
        # Check for triangle patterns
        signals['ascending_triangle'] = self.is_ascending_triangle(closes, swing_highs, swing_lows)
        signals['descending_triangle'] = self.is_descending_triangle(closes, swing_highs, swing_lows)
        
        # Check for flag patterns
        signals['bullish_flag'] = self.is_flag_pattern(closes, "bullish")
        signals['bearish_flag'] = self.is_flag_pattern(closes, "bearish")
        
        # Check for wedge pattern
        signals['wedge'] = self.is_wedge_pattern(closes, swing_highs, swing_lows)
        
        # Check for double top/bottom
        signals['double_top'] = self.is_double_top(closes, swing_highs)
        signals['double_bottom'] = self.is_double_bottom(closes, swing_lows)
        
        return signals