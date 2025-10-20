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

# Strategy Configuration
COMBINED_STRATEGY_WEIGHTS = {
    'macd': float(os.getenv("MACD_WEIGHT", "1.0")),
    'rsi': float(os.getenv("RSI_WEIGHT", "1.0")),
    'momentum': float(os.getenv("MOMENTUM_WEIGHT", "1.0")),
    'candlestick': float(os.getenv("CANDLESTICK_WEIGHT", "1.5")),
    'chart': float(os.getenv("CHART_PATTERN_WEIGHT", "1.5"))
}

TREND_CONFIRMATION_REQUIRED = os.getenv("TREND_CONFIRMATION_REQUIRED", "true").lower() == "true"
MIN_PATTERN_CONFIDENCE = float(os.getenv("MIN_PATTERN_CONFIDENCE", "0.6"))
VOLATILITY_FILTER_ENABLED = os.getenv("VOLATILITY_FILTER_ENABLED", "true").lower() == "true"
VOLUME_FILTER_ENABLED = os.getenv("VOLUME_FILTER_ENABLED", "true").lower() == "true"

# Advanced Trade Management
ENABLE_TRAILING_STOP = os.getenv("ENABLE_TRAILING_STOP", "true").lower() == "true"
ENABLE_DYNAMIC_TARGETS = os.getenv("ENABLE_DYNAMIC_TARGETS", "true").lower() == "true"
ENABLE_VOLATILITY_ADJUSTMENT = os.getenv("ENABLE_VOLATILITY_ADJUSTMENT", "true").lower() == "true"

# Volatility Indicators
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
BOLLINGER_PERIOD = int(os.getenv("BOLLINGER_PERIOD", "20"))
BOLLINGER_STD = float(os.getenv("BOLLINGER_STD", "2.0"))
VOLATILITY_WINDOW = int(os.getenv("VOLATILITY_WINDOW", "20"))
VOLATILITY_STD_MULTIPLIER = float(os.getenv("VOLATILITY_STD_MULTIPLIER", "2.5"))

# Stop Loss Configuration
TRAILING_STOP_TYPE = os.getenv("TRAILING_STOP_TYPE", "atr")  # 'fixed', 'atr', or 'percent'
TRAILING_STOP_VALUE = float(os.getenv("TRAILING_STOP_VALUE", "2.0"))  # ATR multiplier or fixed percentage
TRAILING_ACTIVATION_PCT = float(os.getenv("TRAILING_ACTIVATION_PCT", "0.01"))  # 1% price move to activate

# Take Profit Configuration
PROFIT_TAKING_TYPE = os.getenv("PROFIT_TAKING_TYPE", "dynamic")  # 'fixed' or 'dynamic'
MIN_PROFIT_MULTIPLIER = float(os.getenv("MIN_PROFIT_MULTIPLIER", "1.5"))
MAX_PROFIT_MULTIPLIER = float(os.getenv("MAX_PROFIT_MULTIPLIER", "3.0"))
MAX_DRAWDOWN_PCT = float(os.getenv("MAX_DRAWDOWN_PCT", "0.05"))  # 5% maximum drawdown
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