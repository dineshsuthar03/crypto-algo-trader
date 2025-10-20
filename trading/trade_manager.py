from datetime import datetime
import numpy as np
from collections import deque
from core.config import (
    ENABLE_TRAILING_STOP, ENABLE_DYNAMIC_TARGETS, ENABLE_VOLATILITY_ADJUSTMENT,
    ATR_PERIOD, BOLLINGER_PERIOD, BOLLINGER_STD, VOLATILITY_WINDOW,
    VOLATILITY_STD_MULTIPLIER, TRAILING_STOP_TYPE, TRAILING_STOP_VALUE,
    TRAILING_ACTIVATION_PCT, PROFIT_TAKING_TYPE, MIN_PROFIT_MULTIPLIER,
    MAX_PROFIT_MULTIPLIER, MAX_DRAWDOWN_PCT
)
from core.logger import get_logger

logger = get_logger()

class TradeManager:
    """
    Advanced trade management system with multiple volatility measures
    Features:
    - Multiple volatility indicators (ATR, Bollinger Bands, Historical Volatility)
    - Configurable trailing stops and take-profits
    - Dynamic position management based on market conditions
    - Risk-adjusted position sizing
    """
    
    def __init__(self, initial_price, side):
        # Initialize from config
        self.enable_trailing = ENABLE_TRAILING_STOP
        self.enable_dynamic_targets = ENABLE_DYNAMIC_TARGETS
        self.enable_volatility_adjustment = ENABLE_VOLATILITY_ADJUSTMENT
        
        # Core parameters from config
        self.min_profit_multiplier = MIN_PROFIT_MULTIPLIER
        self.max_profit_multiplier = MAX_PROFIT_MULTIPLIER
        self.trailing_activation_pct = TRAILING_ACTIVATION_PCT
        self.trailing_stop_type = TRAILING_STOP_TYPE
        self.trailing_stop_value = TRAILING_STOP_VALUE
        
        # Price tracking
        self.initial_price = float(initial_price)
        self.side = side.upper()
        self.highest_price = initial_price
        self.lowest_price = initial_price
        
        # Volatility tracking
        self.price_history = deque([initial_price], maxlen=max(ATR_PERIOD, BOLLINGER_PERIOD, VOLATILITY_WINDOW))
        self.high_prices = deque([initial_price], maxlen=ATR_PERIOD)
        self.low_prices = deque([initial_price], maxlen=ATR_PERIOD)
        self.returns = deque([0.0], maxlen=VOLATILITY_WINDOW)
        
        # Technical indicators
        self.atr = 0.0
        self.bollinger_upper = initial_price
        self.bollinger_lower = initial_price
        self.historical_volatility = 0.0
        
        # Stop and target levels
        self.current_stop = initial_price * (1 - VOLATILITY_STD_MULTIPLIER * 0.001)
        self.current_target = None
        self.trailing_activated = False
        # Initialize state
        self.last_update_time = datetime.now()
        self.profit_points = []
        self.loss_points = []
        
    def update_volatility_metrics(self, high, low, close):
        """
        Update all volatility metrics:
        - ATR (Average True Range)
        - Bollinger Bands
        - Historical Volatility
        """
        # Update price data
        self.high_prices.append(high)
        self.low_prices.append(low)
        self.price_history.append(close)
        
        # Calculate price returns for volatility
        if len(self.price_history) >= 2:
            returns = np.log(close / self.price_history[-2])
            self.returns.append(returns)
        
        # Remove old data points if needed
        if len(self.high_prices) > ATR_PERIOD:
            self.high_prices.popleft()
            self.low_prices.popleft()
        if len(self.price_history) > max(ATR_PERIOD, BOLLINGER_PERIOD):
            self.price_history.popleft()
        
        # Need at least 2 data points
        if len(self.price_history) < 2:
            return
        
        # Calculate ATR
        true_ranges = []
        for i in range(1, len(self.price_history)):
            if len(self.high_prices) <= i or len(self.low_prices) <= i:
                continue
            prev_close = list(self.price_history)[i-1]
            curr_high = list(self.high_prices)[i] 
            curr_low = list(self.low_prices)[i]
            true_range = max(
                curr_high - curr_low,                 # Current range
                abs(curr_high - prev_close),         # High-prev close
                abs(curr_low - prev_close)           # Low-prev close
            )
            true_ranges.append(true_range)
        
        self.atr = sum(true_ranges) / len(true_ranges) if true_ranges else None
        
        # Calculate Bollinger Bands
        if len(self.price_history) >= BOLLINGER_PERIOD:
            price_array = np.array(list(self.price_history)[-BOLLINGER_PERIOD:])
            sma = np.mean(price_array)
            std = np.std(price_array)
            self.bollinger_upper = sma + (BOLLINGER_STD * std)
            self.bollinger_lower = sma - (BOLLINGER_STD * std)
        
        # Calculate Historical Volatility
        if len(self.returns) >= VOLATILITY_WINDOW:
            returns_array = np.array(list(self.returns))
            self.historical_volatility = np.std(returns_array) * np.sqrt(252)  # Annualized
        
    def calculate_volatility_based_stops(self, current_price):
        """
        Calculate stop-loss and take-profit based on combined volatility metrics
        Uses a weighted approach considering ATR, Bollinger Bands, and Historical Volatility
        """
        # Update volatility metrics
        if not all([self.atr, self.bollinger_upper, self.bollinger_lower, self.historical_volatility]):
            # Use simple fixed percentage for fallback
            return current_price * 0.01  # 1% stop distance
        
        # Normalize historical volatility to price scale
        vol_based_range = current_price * self.historical_volatility / np.sqrt(252)
        
        # Calculate weighted volatility measure
        volatility_stop = (
            0.4 * self.atr +                    # ATR component
            0.3 * (self.bollinger_upper - self.bollinger_lower) / 2 +  # Bollinger component
            0.3 * vol_based_range               # Historical volatility component
        )
        
        # Adjust stop distance based on configuration
        if TRAILING_STOP_TYPE == 'fixed':
            stop_distance = TRAILING_STOP_VALUE
        elif TRAILING_STOP_TYPE == 'atr':
            stop_distance = volatility_stop
        else:  # 'percent'
            stop_distance = current_price * (TRAILING_STOP_VALUE / 100)
        
        return stop_distance

    def calculate_dynamic_levels(self, current_price, current_high, current_low):
        """Calculate dynamic stop-loss and take-profit levels using all volatility metrics"""
        
        # Update all volatility metrics
        self.update_volatility_metrics(current_high, current_low, current_price)
        
        # Update price extremes
        if self.side == "BUY":
            self.highest_price = max(self.highest_price, current_price)
            price_movement = (current_price - self.initial_price) / self.initial_price
        else:
            self.lowest_price = min(self.lowest_price, current_price)
            price_movement = (self.initial_price - current_price) / self.initial_price
        
        # Check if trailing stop should be activated
        if not self.trailing_activated and price_movement >= TRAILING_ACTIVATION_PCT:
            self.trailing_activated = True
            logger.info(f"Trailing stop activated at {price_movement:.2%} move")
        
        # Get volatility-based stop distance
        stop_distance = self.calculate_volatility_based_stops(current_price)
        
        if self.side == "BUY":
            # For long positions
            if self.trailing_activated:
                # Use trailing stop after activation
                new_stop = current_price - stop_distance
                self.current_stop = max(new_stop, self.current_stop or 0)
            else:
                # Initial stop-loss
                self.current_stop = self.initial_price - stop_distance
            
            # Set take-profit based on configuration
            if PROFIT_TAKING_TYPE == 'fixed':
                profit_distance = current_price * (MAX_PROFIT_MULTIPLIER / 100)
            else:  # 'dynamic'
                profit_distance = stop_distance * MAX_PROFIT_MULTIPLIER
            
            self.current_target = current_price + profit_distance
            
        else:  # SELL
            if self.trailing_activated:
                new_stop = current_price + stop_distance
                self.current_stop = min(new_stop, self.current_stop or float('inf'))
            else:
                self.current_stop = self.initial_price + stop_distance
            
            if PROFIT_TAKING_TYPE == 'fixed':
                profit_distance = current_price * (MAX_PROFIT_MULTIPLIER / 100)
            else:  # 'dynamic'
                profit_distance = stop_distance * MAX_PROFIT_MULTIPLIER
            
            self.current_target = current_price - profit_distance
        
        return self.current_stop, self.current_target
        
    def calculate_basic_levels(self, current_price):
        """Calculate basic stop and target levels without ATR"""
        price_change = abs(current_price - self.initial_price)
        basic_stop = price_change * 0.5  # 50% of the price move
        
        if self.side == "BUY":
            stop_level = max(
                current_price - basic_stop,
                self.current_stop if self.current_stop else current_price * 0.99
            )
            target_level = current_price + (basic_stop * self.min_profit_multiplier)
        else:
            stop_level = min(
                current_price + basic_stop,
                self.current_stop if self.current_stop else current_price * 1.01
            )
            target_level = current_price - (basic_stop * self.min_profit_multiplier)
            
        return stop_level, target_level
        
    def calculate_atr_based_levels(self, current_price):
        """Calculate ATR-based stop and target levels"""
        
        # Base stop distance on ATR
        stop_distance = self.atr * self.trailing_stop_multiplier
        
        if self.side == "BUY":
            # For long positions
            # Trail stop below current price
            new_stop = current_price - stop_distance
            
            # Move stop up if price moves up
            if not self.current_stop or new_stop > self.current_stop:
                self.current_stop = new_stop
                
            # Dynamic take-profit based on volatility
            profit_distance = stop_distance * self.max_profit_multiplier
            self.current_target = current_price + profit_distance
            
        else:
            # For short positions
            # Trail stop above current price
            new_stop = current_price + stop_distance
            
            # Move stop down if price moves down
            if not self.current_stop or new_stop < self.current_stop:
                self.current_stop = new_stop
                
            # Dynamic take-profit based on volatility
            profit_distance = stop_distance * self.max_profit_multiplier
            self.current_target = current_price - profit_distance
            
        return self.current_stop, self.current_target
        
    def should_exit(self, current_price):
        """
        Enhanced exit determination using multiple factors:
        - Trailing stop-loss
        - Dynamic take-profit
        - Volatility-based exits
        - Maximum drawdown protection
        Returns: (bool, str) - (should_exit, reason)
        """
        if not self.current_stop or not self.current_target:
            return False, None

        # Calculate current drawdown
        if self.side == "BUY":
            drawdown = (self.highest_price - current_price) / self.highest_price
            # Check trailing stop
            if current_price <= self.current_stop:
                return True, "TRAILING_STOP"
            # Check take-profit
            if current_price >= self.current_target:
                return True, "TAKE_PROFIT"
            # Check Bollinger Band exit
            if self.bollinger_lower and current_price < self.bollinger_lower:
                return True, "VOLATILITY_BREAKDOWN"
                
        else:  # SELL
            drawdown = (current_price - self.lowest_price) / self.lowest_price
            # Check trailing stop
            if current_price >= self.current_stop:
                return True, "TRAILING_STOP"
            # Check take-profit
            if current_price <= self.current_target:
                return True, "TAKE_PROFIT"
            # Check Bollinger Band exit
            if self.bollinger_upper and current_price > self.bollinger_upper:
                return True, "VOLATILITY_BREAKOUT"
        
        # Check maximum drawdown
        if drawdown >= MAX_DRAWDOWN_PCT:
            return True, "MAX_DRAWDOWN"
            
        # Check volatility expansion exit
        if self.historical_volatility and self.historical_volatility > (VOLATILITY_STD_MULTIPLIER * np.mean(list(self.returns))):
            return True, "VOLATILITY_EXPANSION"
            
        return False, None