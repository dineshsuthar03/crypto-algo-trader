import numpy as np
from collections import defaultdict
from strategy.base_strategy import BaseStrategy
from strategy.macd_strategy import MACDStrategy
from strategy.rsi_strategy import RSIStrategy
from strategy.candlestick_patterns import CandlestickPatterns
from strategy.chart_patterns import ChartPatterns
from strategy.momentum_strategy import MomentumStrategy
from core.config import (
    COMBINED_STRATEGY_WEIGHTS,
    TREND_CONFIRMATION_REQUIRED,
    MIN_PATTERN_CONFIDENCE,
    VOLATILITY_FILTER_ENABLED,
    VOLUME_FILTER_ENABLED
)
from core.logger import get_logger

logger = get_logger()

class CombinedStrategy(BaseStrategy):
    """
    Advanced strategy that combines multiple technical indicators and patterns
    Features:
    - Multiple timeframe analysis
    - Trend confirmation
    - Pattern recognition
    - Volume and volatility filters
    """
    
    def __init__(self):
        super().__init__()
        # Initialize sub-strategies
        self.macd = MACDStrategy()
        self.rsi = RSIStrategy()
        self.candlestick = CandlestickPatterns()
        self.chart = ChartPatterns()
        self.momentum = MomentumStrategy()
        
        # Strategy weights from config
        self.weights = COMBINED_STRATEGY_WEIGHTS
        
        # Initialize signals storage
        self.signals = defaultdict(dict)
        self.trend_signals = defaultdict(str)
        
    def calculate_volatility(self, candles, window=20):
        """Calculate price volatility"""
        if len(candles) < window:
            return None
            
        closes = np.array([c['close'] for c in candles])
        returns = np.log(closes[1:] / closes[:-1])
        return np.std(returns) * np.sqrt(252)  # Annualized volatility
        
    def calculate_volume_trend(self, candles, window=20):
        """Analyze volume trend"""
        if len(candles) < window:
            return None
            
        volumes = np.array([c['volume'] for c in candles])
        avg_volume = np.mean(volumes[-window:])
        current_volume = volumes[-1]
        
        return current_volume / avg_volume
        
    def identify_trend(self, candles):
        """
        Identify overall trend using multiple methods
        Returns: "BULLISH", "BEARISH", or "NEUTRAL"
        """
        if len(candles) < 50:
            return "NEUTRAL"
            
        closes = np.array([c['close'] for c in candles])
        
        # Calculate multiple SMAs
        sma20 = np.mean(closes[-20:])
        sma50 = np.mean(closes[-50:])
        
        # Calculate price momentum
        momentum = closes[-1] / closes[-20] - 1
        
        # Count signals
        bullish_signals = 0
        bearish_signals = 0
        
        # Price above/below SMAs
        if closes[-1] > sma20:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if closes[-1] > sma50:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        # SMA alignment
        if sma20 > sma50:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        # Momentum
        if momentum > 0.02:  # 2% momentum
            bullish_signals += 1
        elif momentum < -0.02:
            bearish_signals += 1
            
        # Determine trend
        if bullish_signals >= 3:
            return "BULLISH"
        elif bearish_signals >= 3:
            return "BEARISH"
        else:
            return "NEUTRAL"
            
    def calculate_pattern_confidence(self, candles):
        """Calculate confidence score for pattern signals"""
        confidence = 0
        
        # Get candlestick patterns
        candlestick_signals = self.candlestick.analyze(candles)
        chart_signals = self.chart.analyze(candles)
        
        if candlestick_signals is None or chart_signals is None:
            return 0
            
        # Count confirmed patterns
        pattern_count = sum(1 for v in candlestick_signals.values() if v)
        pattern_count += sum(1 for v in chart_signals.values() if v)
        
        # Add confidence based on pattern confluence
        confidence += pattern_count * 0.2  # 20% per pattern
        
        # Add confidence for trend alignment
        trend = self.identify_trend(candles)
        if trend != "NEUTRAL":
            if trend == "BULLISH" and any(s for s in candlestick_signals.values() if s == "BULLISH"):
                confidence += 0.3
            elif trend == "BEARISH" and any(s for s in candlestick_signals.values() if s == "BEARISH"):
                confidence += 0.3
                
        return min(confidence, 1.0)  # Cap at 100%
        
    def should_filter_signal(self, candles):
        """Apply volume and volatility filters"""
        if VOLATILITY_FILTER_ENABLED:
            volatility = self.calculate_volatility(candles)
            if volatility is None or volatility < 0.15:  # Min 15% annualized volatility
                return True
                
        if VOLUME_FILTER_ENABLED:
            volume_trend = self.calculate_volume_trend(candles)
            if volume_trend is None or volume_trend < 1.0:  # Require above average volume
                return True
                
        return False
        
    def analyze(self, candles):
        """
        Combined analysis using all strategies
        Returns weighted signals and confidence scores
        """
        if len(candles) < 50:  # Minimum required candles
            return None
            
        # Reset signals
        self.signals.clear()
        
        # Apply filters
        if self.should_filter_signal(candles):
            return None
            
        # Get trend context
        trend = self.identify_trend(candles)
        
        # Calculate confidence score
        pattern_confidence = self.calculate_pattern_confidence(candles)
        
        if TREND_CONFIRMATION_REQUIRED and trend == "NEUTRAL":
            return None
            
        if pattern_confidence < MIN_PATTERN_CONFIDENCE:
            return None
            
        # Collect signals from all strategies
        signals = {
            'macd': self.macd.analyze(candles),
            'rsi': self.rsi.analyze(candles),
            'momentum': self.momentum.analyze(candles),
            'candlestick': self.candlestick.analyze(candles),
            'chart': self.chart.analyze(candles)
        }
        
        # Apply weights and calculate final signal
        weighted_bullish = 0
        weighted_bearish = 0
        
        for strategy, signal in signals.items():
            if signal is None:
                continue
                
            weight = self.weights.get(strategy, 1.0)
            
            if isinstance(signal, dict):
                # Handle pattern signals
                for pattern, value in signal.items():
                    if value == "BULLISH":
                        weighted_bullish += weight
                    elif value == "BEARISH":
                        weighted_bearish += weight
            else:
                # Handle simple signals
                if signal == "BULLISH":
                    weighted_bullish += weight
                elif signal == "BEARISH":
                    weighted_bearish += weight
                    
        # Calculate final signal
        final_signal = None
        if weighted_bullish > weighted_bearish and weighted_bullish >= 2.0:
            final_signal = "BULLISH"
        elif weighted_bearish > weighted_bullish and weighted_bearish >= 2.0:
            final_signal = "BEARISH"
            
        if final_signal:
            logger.info(f"Combined strategy signal: {final_signal} "
                       f"(Confidence: {pattern_confidence:.2f}, Trend: {trend})")
            
        return final_signal