# TODO: Implement this module
import threading
import time
from datetime import datetime
from core.config import TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC, REFRESH_INTERVAL
import random  # For mock live price
import redis
from core.config import REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL, TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

class Position:
    def __init__(self, symbol, side, entry_price):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.open_time = datetime.now()
        self.closed = False

class PositionTracker:
    def __init__(self):
        self.positions = []

    def open_position(self, symbol, side, entry_price):
        pos = Position(symbol, side, entry_price)
        self.positions.append(pos)
        t = threading.Thread(target=self.monitor_position, args=(pos,))
        t.daemon = True
        t.start()

    def monitor_position(self, pos):
        while not pos.closed:
            # Get latest LTP from Redis
            ltp = r.get(f"LTP:{pos.symbol}")
            if ltp is None:
                time.sleep(REFRESH_INTERVAL)
                continue
            live_price = float(ltp)

            pnl_percent = ((live_price - pos.entry_price) / pos.entry_price) * 100
            if pos.side.lower() == "sell":
                pnl_percent *= -1  # reverse PnL for short

            elapsed = (datetime.now() - pos.open_time).seconds

            # Check exit conditions
            if pnl_percent >= TARGET_PERCENT:
                print(f"✅ TARGET HIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
                pos.closed = True
            elif pnl_percent <= -STOPLOSS_PERCENT:
                print(f"❌ STOPLOSS HIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
                pos.closed = True
            elif elapsed >= MAX_HOLD_TIME_SEC:
                print(f"⏰ TIME EXIT | {pos.symbol} @ {live_price} | PnL: {pnl_percent:.2f}%")
                pos.closed = True

            time.sleep(REFRESH_INTERVAL)

    def get_open_positions(self):
        return [p for p in self.positions if not p.closed]
