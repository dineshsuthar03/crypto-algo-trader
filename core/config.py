import os
from dotenv import load_dotenv

load_dotenv()

# Testnet/Production
USE_TESTNET = os.getenv("USE_TESTNET", "false").lower() == "true"

# Binance Credentials
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Symbols & Market Types
SYMBOLS = os.getenv("SYMBOLS").split(",")
MARKET_TYPES = os.getenv("MARKET_TYPES").split(",")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

# Strategy Parameters
TARGET_PERCENT = float(os.getenv("TARGET_PERCENT"))
STOPLOSS_PERCENT = float(os.getenv("STOPLOSS_PERCENT"))
MAX_HOLD_TIME_SEC = int(os.getenv("MAX_HOLD_TIME_SEC"))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL"))

# Exit Strategy Configuration
EXIT_STRATEGY_SIGNAL_PRIORITY = int(os.getenv("EXIT_STRATEGY_SIGNAL_PRIORITY", "1"))
EXIT_TARGET_PRIORITY = int(os.getenv("EXIT_TARGET_PRIORITY", "2"))
EXIT_STOPLOSS_PRIORITY = int(os.getenv("EXIT_STOPLOSS_PRIORITY", "3"))
EXIT_TIME_PRIORITY = int(os.getenv("EXIT_TIME_PRIORITY", "4"))

# Exit Strategy Enable/Disable
EXIT_STRATEGY_SIGNAL_ENABLE = os.getenv("EXIT_STRATEGY_SIGNAL_ENABLE", "true").lower() == "true"
EXIT_TARGET_ENABLE = os.getenv("EXIT_TARGET_ENABLE", "true").lower() == "true"
EXIT_STOPLOSS_ENABLE = os.getenv("EXIT_STOPLOSS_ENABLE", "true").lower() == "true"
EXIT_TIME_ENABLE = os.getenv("EXIT_TIME_ENABLE", "true").lower() == "true"

# Trading Parameters
TRADE_AMOUNT_USDT = float(os.getenv("TRADE_AMOUNT_USDT", "20"))  # Amount in USDT per trade
MIN_NOTIONAL = float(os.getenv("MIN_NOTIONAL", "10"))  # Binance minimum notional
SPOT_COMMISSION_RATE = float(os.getenv("SPOT_COMMISSION_RATE", "0.001"))  # 0.1% trading fee
FUTURES_COMMISSION_RATE = float(os.getenv("FUTURES_COMMISSION_RATE", "0.0004"))  # 0.04% futures fee

# Position Management
MAX_POSITIONS_PER_SYMBOL = int(os.getenv("MAX_POSITIONS_PER_SYMBOL", "1"))
ENABLE_SCALING = os.getenv("ENABLE_SCALING", "false").lower() == "true"

# Price Precision (for different coins)
PRICE_PRECISION = {
    "SHIBUSDT": 8,
    "DOGEUSDT": 5,
    "PEPEUSDT": 10,
    "BTCUSDT": 2,
    "ETHUSDT": 2
}

QUANTITY_PRECISION = {
    "SHIBUSDT": 0,
    "DOGEUSDT": 0,
    "PEPEUSDT": 0,
    "BTCUSDT": 3,
    "ETHUSDT": 3
}