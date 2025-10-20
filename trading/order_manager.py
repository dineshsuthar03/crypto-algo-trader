# # TODO: Implement this module
# from datetime import datetime
# from trading.position_tracker import PositionTracker

# # Initialize global position tracker
# tracker = PositionTracker()

# def place_order(symbol, side, price):
#     """
#     Mock order placement
#     """
#     print(f"[{datetime.now().strftime('%H:%M:%S')}] {side.upper()} ORDER | {symbol} @ {price}")
#     tracker.open_position(symbol, side, price)



# from trading.position_tracker import tracker
# from core.config import BINANCE_API_KEY, BINANCE_API_SECRET
# from binance.client import Client

# client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# def place_order(symbol, side, price, market_type, strategy="Breakout"):
#     print(f"Placing {market_type.upper()} {side.upper()} order | {symbol} @ {price}")
#     tracker.open_position(symbol, side, price, market_type)
    
#     # ---------------- Example REST API call (mock) ----------------
#     try:
#         if market_type == "spot":
#             order = client.create_order(
#                 symbol=symbol,
#                 side=side.upper(),
#                 type="MARKET",
#                 quantity=0.001  # replace with dynamic qty calculation
#             )
#         else:
#             # Futures order
#             order = client.futures_create_order(
#                 symbol=symbol,
#                 side=side.upper(),
#                 type="MARKET",
#                 quantity=0.001
#             )
#         print(" Binance Order Executed:", order)
#     except Exception as e:
#         print(" Binance Order Error:", e)



from trading.position_tracker import tracker
from core.config import BINANCE_API_KEY, BINANCE_API_SECRET,USE_TESTNET
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from binance.client import Client
from core.logger import get_logger
logger = get_logger()



client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
if USE_TESTNET:
    client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'
def place_order(symbol, side, price, market_type, strategy="Breakout"):
    logger.info(f"Placing {market_type.upper()} {side.upper()} order | {symbol} @ {price}")
    tracker.open_position(symbol, side, price, market_type, strategy)
    try:
        if market_type == "spot":
            order = client.create_order(
                symbol=symbol,
                side=side.upper(),
                type="MARKET",
                quantity=0.001
            )
        else:
            order = client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type="MARKET",
                quantity=0.001
            )
        logger.info(f" Binance Order Executed: {order}")
        logger.info(f" Binance Order Executed: ")
    except Exception as e:
        logger.error(f" Binance Order Error: {e}")





# # ...existing code...
# from core.logger import get_logger
# logger = get_logger()

# # confirm module load
# logger.info("order_manager module loaded")
# # confirm module load
# logger.info("order_manager module loaded")
# print("order_manager module loaded (print) ->", __file__)

# # ...existing code...
# def place_order(symbol, side, price, market_type, strategy="Breakout"):
#     logger.info(f"place_order called -> symbol={symbol} side={side} price={price} market_type={market_type} strategy={strategy}")
#     tracker.open_position(symbol, side, price, market_type, strategy)
#     try:
#         logger.debug("About to send order to Binance client (mocked)")
#         # ...existing code...
#         logger.info(f" Binance Order Executed: ")
#     except Exception as e:
#         logger.exception(f" Binance Order Error: {e}")
# # ...existing code...