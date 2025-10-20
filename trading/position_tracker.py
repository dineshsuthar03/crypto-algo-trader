# # TODO: Implement this module
import threading
import time
from datetime import datetime
from core.config import TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC, REFRESH_INTERVAL
import random  # For mock live price
import redis
# from core.config import REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL, TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC

# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# class Position:
#     def __init__(self, symbol, side, entry_price):
#         self.symbol = symbol
#         self.side = side
#         self.entry_price = entry_price
#         self.open_time = datetime.now()
#         self.closed = False

# class PositionTracker:
#     def __init__(self):
#         self.positions = []

#     def open_position(self, symbol, side, entry_price):
#         pos = Position(symbol, side, entry_price)
#         self.positions.append(pos)
#         t = threading.Thread(target=self.monitor_position, args=(pos,))
#         t.daemon = True
#         t.start()

#     def monitor_position(self, pos):
#         while not pos.closed:
#             # Get latest LTP from Redis
#             ltp = r.get(f"LTP:{pos.symbol}")
#             if ltp is None:
#                 time.sleep(REFRESH_INTERVAL)
#                 continue
#             live_price = float(ltp)

#             pnl_percent = ((live_price - pos.entry_price) / pos.entry_price) * 100
#             if pos.side.lower() == "sell":
#                 pnl_percent *= -1  # reverse PnL for short

#             elapsed = (datetime.now() - pos.open_time).seconds

#             # Check exit conditions
#             if pnl_percent >= TARGET_PERCENT:
#                 print(f" TARGET HIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
#                 pos.closed = True
#             elif pnl_percent <= -STOPLOSS_PERCENT:
#                 print(f" STOPLOSS HIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
#                 pos.closed = True
#             elif elapsed >= MAX_HOLD_TIME_SEC:
#                 print(f"⏰ TIME EXIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
#                 pos.closed = True

#             time.sleep(REFRESH_INTERVAL)

#     def get_open_positions(self):
#         return [p for p in self.positions if not p.closed]



# # # # TODO: Implement this module
# # import threading
# import time
# from datetime import datetime
# # from core.config import TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC, REFRESH_INTERVAL
# # import random  # For mock live price
# import redis
# from core.config import REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL, TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC

# from storage.mongo_handler import log_trade
# import redis, threading, time
# from core.config import REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL, TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC

# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# class Position:
#     def __init__(self, symbol, side, entry_price, market_type):
#         self.symbol = symbol
#         self.side = side
#         self.entry_price = entry_price
#         self.market_type = market_type
#         self.open_time = datetime.now()
#         self.closed = False

# class PositionTracker:
#     def __init__(self):
#         self.positions = []

#     def open_position(self, symbol, side, price, market_type):
#         pos = Position(symbol, side, price, market_type)
#         self.positions.append(pos)
#         t = threading.Thread(target=self.monitor_position, args=(pos,))
#         t.daemon = True
#         t.start()

    # def monitor_position(self, pos):
    #     while not pos.closed:
    #         ltp = r.get(f"LTP:{pos.symbol}")
    #         if ltp is None:
    #             time.sleep(REFRESH_INTERVAL)
    #             continue
    #         live_price = float(ltp)

    #         pnl = ((live_price - pos.entry_price)/pos.entry_price)*100
    #         if pos.side.lower() == "sell" or pos.market_type=="futures" and pos.side=="short":
    #             pnl *= -1

    #         elapsed = (datetime.now() - pos.open_time).seconds

    #         if pnl >= TARGET_PERCENT or pnl <= -STOPLOSS_PERCENT or elapsed >= MAX_HOLD_TIME_SEC:
    #             reason = "TARGET" if pnl>=TARGET_PERCENT else "STOPLOSS" if pnl<=-STOPLOSS_PERCENT else "TIME EXIT"
    #             print(f"{reason} | {pos.symbol} @ {live_price:.2f} | PnL: {pnl:.2f}%")
    #             pos.closed = True

    



#     def monitor_position(self, pos):
#         while not pos.closed:
#             ltp = r.get(f"LTP:{pos.symbol}")
#             if ltp is None:
#                 time.sleep(REFRESH_INTERVAL)
#                 continue
#             live_price = float(ltp)

#             pnl = ((live_price - pos.entry_price)/pos.entry_price)*100
#             if pos.side.lower() == "sell" or (pos.market_type=="futures" and pos.side=="short"):
#                 pnl *= -1

#             elapsed = (datetime.now() - pos.open_time).seconds

#             exit_reason = None
#             if pnl >= TARGET_PERCENT:
#                 exit_reason = "TARGET"
#             elif pnl <= -STOPLOSS_PERCENT:
#                 exit_reason = "STOPLOSS"
#             elif elapsed >= MAX_HOLD_TIME_SEC:
#                 exit_reason = "TIME EXIT"

#             if exit_reason:
#                 print(f"{exit_reason} | {pos.symbol} @ {live_price:.2f} | PnL: {pnl:.2f}%")
#                 pos.closed = True

#                 # Log trade in Mongo
#                 trade_data = {
#                     "symbol": pos.symbol,
#                     "market_type": pos.market_type,
#                     "side": pos.side,
#                     "entry_price": pos.entry_price,
#                     "exit_price": live_price,
#                     "entry_time": pos.open_time,
#                     "exit_time": datetime.now(),
#                     "pnl_percent": pnl,
#                     "reason": exit_reason,
#                     "strategy": getattr(pos, "strategy", "unknown")
#                 }
#                 log_trade(trade_data)


# def place_order(symbol, side, price, market_type):
#     print(f"Placing {market_type.upper()} {side.upper()} order | {symbol} @ {price}")
#     tracker.open_position(symbol, side, price, market_type)

# tracker = PositionTracker()









import redis, threading, time
from datetime import datetime
from core.config import REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL, TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC
from storage.mongo_handler import log_trade
from core.logger import get_logger
logger = get_logger()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

class Position:
    def __init__(self, symbol, side, entry_price, market_type, strategy="Breakout"):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.market_type = market_type
        self.strategy = strategy
        self.open_time = datetime.now()
        self.closed = False

class PositionTracker:
    def __init__(self):
        self.positions = []

    def open_position(self, symbol, side, price, market_type, strategy="Breakout"):
        pos = Position(symbol, side, price, market_type, strategy)
        self.positions.append(pos)
        t = threading.Thread(target=self.monitor_position, args=(pos,))
        t.daemon = True
        t.start()

    def monitor_position(self, pos):
        while not pos.closed:
            ltp = r.get(f"LTP:{pos.symbol}")
            if ltp is None:
                time.sleep(REFRESH_INTERVAL)
                continue
            live_price = float(ltp)

            pnl = ((live_price - pos.entry_price)/pos.entry_price)*100
            if pos.side.lower() == "sell" or (pos.market_type=="futures" and pos.side=="short"):
                pnl *= -1

            elapsed = (datetime.now() - pos.open_time).seconds

            exit_reason = None
            if pnl >= TARGET_PERCENT:
                exit_reason = "TARGET"
            elif pnl <= -STOPLOSS_PERCENT:
                exit_reason = "STOPLOSS"
            elif elapsed >= MAX_HOLD_TIME_SEC:
                exit_reason = "TIME EXIT"

            if exit_reason:
                print(f"{exit_reason} | {pos.symbol} @ {live_price:.2f} | PnL: {pnl:.2f}%")
                logger.info(f"{exit_reason} | {pos.symbol} @ {live_price:.2f} | PnL: {pnl:.2f}%")

                pos.closed = True

                trade_data = {
                    "symbol": pos.symbol,
                    "market_type": pos.market_type,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "exit_price": live_price,
                    "entry_time": pos.open_time,
                    "exit_time": datetime.now(),
                    "pnl_percent": pnl,
                    "reason": exit_reason,
                    "strategy": pos.strategy
                }
                log_trade(trade_data)

tracker = PositionTracker()
