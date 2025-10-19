# TODO: Implement this module
import time
from datetime import datetime
from collections import deque
import redis
from core.config import REDIS_HOST, REDIS_PORT, SYMBOL

# ----------------- Redis Connection -----------------
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# ----------------- Candle Data Structure -----------------
# Keep last N candles in memory (deque)
MAX_CANDLES = 500
candles = deque(maxlen=MAX_CANDLES)

# Example candle structure:
# {
#   "timestamp": datetime,
#   "open": float,
#   "high": float,
#   "low": float,
#   "close": float,
#   "volume": float
# }

# ----------------- Candle Builder -----------------
current_candle = None

def update_candle(live_tick):
    """
    live_tick = {
        'timestamp': datetime,
        'price': float,
        'volume': float
    }
    """
    global current_candle

    tick_time = live_tick['timestamp']
    tick_price = live_tick['price']
    tick_volume = live_tick.get('volume', 0)

    candle_time = tick_time.replace(second=0, microsecond=0)

    if current_candle is None or current_candle['timestamp'] != candle_time:
        # Close previous candle
        if current_candle:
            candles.append(current_candle)
            # Store in Redis
            r.set(f"{SYMBOL}_{current_candle['timestamp']}", str(current_candle))

        # Start new candle
        current_candle = {
            "timestamp": candle_time,
            "open": tick_price,
            "high": tick_price,
            "low": tick_price,
            "close": tick_price,
            "volume": tick_volume
        }
    else:
        # Update current candle
        current_candle['high'] = max(current_candle['high'], tick_price)
        current_candle['low'] = min(current_candle['low'], tick_price)
        current_candle['close'] = tick_price
        current_candle['volume'] += tick_volume

def get_last_candle():
    """Return the most recently closed candle"""
    if candles:
        return candles[-1]
    return None

def get_all_candles():
    """Return all in-memory candles"""
    return list(candles)

# ----------------- Mock / Test -----------------
if __name__ == "__main__":
    # Simulate live ticks every second
    import random
    while True:
        tick = {
            "timestamp": datetime.now(),
            "price": round(random.uniform(65000, 66000), 2),
            "volume": round(random.uniform(0.01, 0.5), 3)
        }
        update_candle(tick)
        last = get_last_candle()
        if last:
            print(f"Last Candle: {last}")
        time.sleep(1)
