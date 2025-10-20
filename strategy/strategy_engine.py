# # TODO: Implement this module
# from strategy.breakout_strategy import BreakoutStrategy
# from data_feed import candle_store

# class StrategyEngine:
#     """
#     Loads and executes all active strategies
#     """

#     def __init__(self):
#         # Add more strategies as you implement
#         self.strategies = [BreakoutStrategy()]

#     def run(self):
#         """
#         Run all strategies on the latest closed candle
#         """
#         last_candle = candle_store.get_last_candle()
#         if not last_candle:
#             return None

#         signals = {}
#         for strat in self.strategies:
#             signal = strat.generate_signal(last_candle)
#             signals[type(strat).__name__] = signal

#         return signals


# # ---------------- Test ----------------
# if __name__ == "__main__":
#     engine = StrategyEngine()

#     # Mock: call every second (in real usage, call on new candle)
#     import time
#     import random
#     from datetime import datetime

#     from data_feed import candle_store

#     while True:
#         # Simulate new tick & update candle
#         tick = {
#             "timestamp": datetime.now(),
#             "price": round(random.uniform(65000, 66000), 2),
#             "volume": round(random.uniform(0.01, 0.5), 3)
#         }
#         candle_store.update_candle(tick)

#         signals = engine.run()
#         if signals:
#             print(f"Signals: {signals}")

#         time.sleep(1)





# from strategy.breakout_strategy import BreakoutStrategy
# from data_feed import candle_store
# from core.config import SYMBOLS

# class StrategyEngine:
#     def __init__(self):
#         # One strategy instance per symbol (can add more strategies later)
#         self.strategies = {sym: [BreakoutStrategy()] for sym in SYMBOLS}

#     def run(self):
#         signals = {}
#         for sym in SYMBOLS:
#             candle = candle_store.get_last_candle(sym)
#             if not candle:
#                 continue
#             for strat in self.strategies[sym]:
#                 signal = strat.generate_signal(candle)
#                 signals[(sym, type(strat).__name__)] = signal
#         return signals



from strategy.breakout_strategy import BreakoutStrategy
from data_feed import candle_store
from core.config import SYMBOLS

class StrategyEngine:
    def __init__(self):
        self.strategies = {sym: [BreakoutStrategy()] for sym in SYMBOLS}

    def run(self):
        signals = {}
        for sym in SYMBOLS:
            candle = candle_store.get_last_candle(sym)
            if not candle:
                continue
            for strat in self.strategies[sym]:
                signal = strat.generate_signal(candle)
                signals[(sym, type(strat).__name__)] = signal
        return signals
