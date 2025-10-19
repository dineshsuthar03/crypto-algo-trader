# # TODO: Implement this module
# from data_feed.live_feed import start_ws
# from strategy.strategy_engine import StrategyEngine
# from trading import order_manager
# import threading
# import time

# engine = StrategyEngine()

# def run_strategy_loop():
#     while True:
#         signals = engine.run()
#         if signals:
#             for strat, sig in signals.items():
#                 if sig in ["BUY", "SELL"]:
#                     order_manager.place_order("BTCUSDT", sig, 65000)  # replace 65000 with last candle close
#         time.sleep(1)

# # Start live feed
# ws_thread = threading.Thread(target=start_ws)
# ws_thread.daemon = True
# ws_thread.start()

# # Start strategy loop
# run_strategy_loop()










import threading
import time
from data_feed import live_feed, candle_store
from strategy.strategy_engine import StrategyEngine
from trading import order_manager
# from core.logger import logger  # optional, if you want async logging

# ---------------- Strategy Engine ----------------
engine = StrategyEngine()

def strategy_loop():
    """
    Continuously check for new candles and generate signals.
    """
    last_signal_time = None

    while True:
        last_candle = candle_store.get_last_candle()
        if last_candle:
            # Ensure we only run once per new candle
            if last_signal_time != last_candle['timestamp']:
                last_signal_time = last_candle['timestamp']
                signals = engine.run()
                if signals:
                    for strat, sig in signals.items():
                        if sig in ["BUY", "SELL"]:
                            price = last_candle['close']
                            order_manager.place_order("BTCUSDT", sig, price)
        time.sleep(0.5)  # check twice per second for new candle

# ---------------- Start Live Feed ----------------
ws_thread = threading.Thread(target=live_feed.start_ws)
ws_thread.daemon = True
ws_thread.start()

# ---------------- Start Strategy Loop ----------------
strategy_thread = threading.Thread(target=strategy_loop)
strategy_thread.daemon = True
strategy_thread.start()

# ---------------- Keep Main Alive ----------------
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down trading system...")
    # logger.info("Trading system stopped by user.")