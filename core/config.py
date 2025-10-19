# # TODO: Implement this module
# import os
# from dotenv import load_dotenv

# # Load .env
# load_dotenv()

# # ----------------- Binance Credentials -----------------
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
# BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# # ----------------- Trading Config -----------------
# SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
# INTERVAL = os.getenv("INTERVAL", "1m")
# MARKET_TYPE = os.getenv("MARKET_TYPE", "spot")

# TARGET_PERCENT = float(os.getenv("TARGET_PERCENT", 0.4))
# STOPLOSS_PERCENT = float(os.getenv("STOPLOSS_PERCENT", 0.2))
# MAX_HOLD_TIME_SEC = int(os.getenv("MAX_HOLD_TIME_SEC", 60))
# REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 1))

# # ----------------- Storage -----------------
# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# MONGO_DB = os.getenv("MONGO_DB", "trading_system")





import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# ----------------- Binance Credentials -----------------
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# ----------------- Trading Config -----------------
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
INTERVAL = os.getenv("INTERVAL", "1m")
MARKET_TYPE = os.getenv("MARKET_TYPE", "spot")

TARGET_PERCENT = float(os.getenv("TARGET_PERCENT", 0.4))
STOPLOSS_PERCENT = float(os.getenv("STOPLOSS_PERCENT", 0.2))
MAX_HOLD_TIME_SEC = int(os.getenv("MAX_HOLD_TIME_SEC", 60))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 1))

# ----------------- Storage -----------------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "trading_system")
