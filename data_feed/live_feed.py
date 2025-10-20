# import websocket
# import json
# from datetime import datetime
# import threading
# # import sys
# # sys.path.append("..")  # to access core and data_feed
# from core.config import SYMBOL, INTERVAL, MARKET_TYPE, USE_TESTNET
# from data_feed import candle_store  # import our candle builder
# # Add at the top
# from core.config import REDIS_HOST, REDIS_PORT
# import redis

# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
# # ---------------- WebSocket URL ----------------
# if USE_TESTNET:
#     if MARKET_TYPE == "spot":
#         WS_URL = "wss://stream.testnet.binance.vision/ws"
#     else:
#         WS_URL = "wss://stream.binancefuture.com/ws"
# else:
#     if MARKET_TYPE == "spot":
#         WS_URL = "wss://stream.binance.com:9443/ws"
#     else:
#         WS_URL = "wss://fstream.binance.com/ws"

# STREAM_NAME = f"{SYMBOL.lower()}@kline_{INTERVAL}"

# # ---------------- Callbacks ----------------
# # def on_message(ws, message):
# #     data = json.loads(message)
# #     if 'e' in data and data['e'] == 'kline':
# #         k = data['k']
# #         ts = datetime.fromtimestamp(k['t']/1000)
# #         open_price = float(k['o'])
# #         close_price = float(k['c'])
# #         # print(f"[{ts}] {SYMBOL} | O:{open_price} C:{close_price}")
# #         volume = float(k['v'])

# #         # Build tick dict
# #         tick = {
# #             "timestamp": ts,
# #             "price": close_price,
# #             "volume": volume
# #         }
# #          # Send tick to candle_store
# #         candle_store.update_candle(tick)

# #         # Optional: print live tick / candle info
# #         last_candle = candle_store.get_last_candle()
# #         if last_candle:
# #             print(f"[{last_candle['timestamp']}] O:{last_candle['open']} H:{last_candle['high']} L:{last_candle['low']} C:{last_candle['close']} V:{last_candle['volume']}")





# # ---------------- Modify on_message ----------------
# def on_message(ws, message):
#     data = json.loads(message)
#     if 'e' in data and data['e'] == 'kline':
#         k = data['k']
#         ts = datetime.fromtimestamp(k['t']/1000)
#         close_price = float(k['c'])
#         volume = float(k['v'])

#         tick = {
#             "timestamp": ts,
#             "price": close_price,
#             "volume": volume
#         }

#         # Update candle
#         candle_store.update_candle(tick)

#         # ---------------- Save latest LTP in Redis ----------------
#         r.set(f"LTP:{SYMBOL}", close_price)

#         # Optional: print live candle info
#         last_candle = candle_store.get_last_candle()
#         if last_candle:
#             print(f"[{last_candle['timestamp']}] O:{last_candle['open']} H:{last_candle['high']} L:{last_candle['low']} C:{last_candle['close']} V:{last_candle['volume']}")




# def on_error(ws, error):
#     print(f"WebSocket Error: {error}")

# def on_close(ws, close_status_code, close_msg):
#     print("WebSocket Closed")

# def on_open(ws):
#     print(f"WebSocket Connected | {SYMBOL} @ {INTERVAL}")

# # ---------------- Start WebSocket ----------------
# def start_ws():
#     ws_url = f"{WS_URL}/{STREAM_NAME}"
#     ws = websocket.WebSocketApp(
#         ws_url,
#         on_message=on_message,
#         on_error=on_error,
#         on_close=on_close,
#         on_open=on_open
#     )
#     ws_thread = threading.Thread(target=ws.run_forever, kwargs={'ping_interval': 20, 'ping_timeout': 10})
#     ws_thread.daemon = True
#     ws_thread.start()
#     ws_thread.join()

# # ---------------- Test ----------------
# if __name__ == "__main__":
#     start_ws()



# import websocket
# import json
# from datetime import datetime
# import threading
# import redis
# from core.config import BINANCE_API_KEY, BINANCE_API_SECRET, SYMBOLS, MARKET_TYPES, REDIS_HOST, REDIS_PORT
# from data_feed import candle_store

# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# def start_ws(symbol, market_type):
#     """Start WebSocket for given symbol and market type"""
#     if market_type == "spot":
#         ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1m"
#     else:  # futures
#         ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@kline_1m"

#     def on_message(ws, message):
#         data = json.loads(message)
#         if 'e' in data and data['e'] == 'kline':
#             k = data['k']
#             ts = datetime.fromtimestamp(k['t']/1000)
#             close_price = float(k['c'])
#             volume = float(k['v'])

#             tick = {"timestamp": ts, "price": close_price, "volume": volume}
#             candle_store.update_candle(tick, symbol)  # multi-symbol support

#             # Save latest LTP in Redis per symbol
#             r.set(f"LTP:{symbol}", close_price)

#     ws = websocket.WebSocketApp(ws_url, on_message=on_message)
#     t = threading.Thread(target=ws.run_forever, kwargs={'ping_interval':20, 'ping_timeout':10})
#     t.daemon = True
#     t.start()
#     return t




import websocket, json, threading
from datetime import datetime
import redis
from core.config import REDIS_HOST, REDIS_PORT
from data_feed import candle_store

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def start_ws(symbol, market_type):
    if market_type == "spot":
        ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_1m"
    else:
        ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@kline_1m"

    def on_message(ws, message):
        data = json.loads(message)
        if 'e' in data and data['e'] == 'kline':
            k = data['k']
            ts = datetime.fromtimestamp(k['t']/1000)
            close_price = float(k['c'])
            volume = float(k['v'])

            tick = {"timestamp": ts, "price": close_price, "volume": volume}
            candle_store.update_candle(tick, symbol)
            r.set(f"LTP:{symbol}", close_price)

    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    t = threading.Thread(target=ws.run_forever, kwargs={'ping_interval':20, 'ping_timeout':10})
    t.daemon = True
    t.start()
    return t
