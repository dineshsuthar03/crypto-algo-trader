# # TODO: Implement this module
# from strategy.base_strategy import BaseStrategy

# class BreakoutStrategy(BaseStrategy):
#     """
#     Simple breakout strategy:
#     - Buy if close > previous high
#     - Sell if close < previous low
#     """

#     def __init__(self):
#         self.prev_high = None
#         self.prev_low = None

#     def generate_signal(self, candle):
#         if self.prev_high is None or self.prev_low is None:
#             # First candle, just store values
#             self.prev_high = candle['high']
#             self.prev_low = candle['low']
#             return "NONE"

#         signal = "NONE"
#         if candle['close'] > self.prev_high:
#             signal = "BUY"
#         elif candle['close'] < self.prev_low:
#             signal = "SELL"

#         # Update previous candle values
#         self.prev_high = candle['high']
#         self.prev_low = candle['low']

#         return signal





from strategy.base_strategy import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    def generate_signal(self, candle):
        """
        Simple mock: Buy if close > open, Sell if close < open
        """
        if candle['close'] > candle['open']:
            return "BUY"
        elif candle['close'] < candle['open']:
            return "SELL"
        else:
            return None
