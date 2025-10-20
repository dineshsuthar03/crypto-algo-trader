# from pymongo import MongoClient
# from core.config import MONGO_URI, MONGO_DB

# client = MongoClient(MONGO_URI)
# db = client[MONGO_DB]
# trades_col = db["trades"]

# def log_trade(trade_data: dict):
#     """
#     trade_data = {
#         "symbol": str,
#         "market_type": "spot"/"futures",
#         "side": "BUY"/"SELL",
#         "entry_price": float,
#         "exit_price": float,
#         "entry_time": datetime,
#         "exit_time": datetime,
#         "pnl_percent": float,
#         "reason": "TARGET"/"STOPLOSS"/"TIME EXIT",
#         "strategy": str
#     }
#     """
#     trades_col.insert_one(trade_data)



from pymongo import MongoClient
from core.config import MONGO_URI, MONGO_DB
from datetime import datetime

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
trades_col = db["trades"]

def log_trade(trade_data: dict):
    trade_data["logged_at"] = datetime.now()
    trades_col.insert_one(trade_data)
