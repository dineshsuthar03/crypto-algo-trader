import websocket
import json
from datetime import datetime
from core.config import BINANCE_API_KEY, BINANCE_API_SECRET, SYMBOL, INTERVAL, MARKET_TYPE, USE_TESTNET
import threading

# ---------------- WebSocket URL ----------------
USE_TESTNET = True
if USE_TESTNET:
    if MARKET_TYPE == "spot":
        WS_URL = "wss://stream.testnet.binance.vision/ws"
    else:
        WS_URL = "wss://stream.binancefuture.com/ws"
else:
    if MARKET_TYPE == "spot":
        WS_URL = "wss://stream.binance.com:9443/ws"
    else:
        WS_URL = "wss://fstream.binance.com/ws"

STREAM_NAME = f"{SYMBOL.lower()}@kline_{INTERVAL}"

# ---------------- Callbacks ----------------
def on_message(ws, message):
    data = json.loads(message)
    if 'e' in data and data['e'] == 'kline':
        k = data['k']
        ts = datetime.fromtimestamp(k['t']/1000)
        open_price = float(k['o'])
        close_price = float(k['c'])
        print(f"[{ts}] {SYMBOL} | O:{open_price} C:{close_price}")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket Closed")

def on_open(ws):
    print(f"WebSocket Connected | {SYMBOL} @ {INTERVAL}")

# ---------------- Start WebSocket ----------------
def start_ws():
    ws_url = f"{WS_URL}/{STREAM_NAME}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws_thread = threading.Thread(target=ws.run_forever, kwargs={'ping_interval': 20, 'ping_timeout': 10})
    ws_thread.daemon = True
    ws_thread.start()
    ws_thread.join()

# For testing
if __name__ == "__main__":
    start_ws()
