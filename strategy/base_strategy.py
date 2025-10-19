# TODO: Implement this module
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    Each strategy must implement `generate_signal` method.
    """

    @abstractmethod
    def generate_signal(self, candle):
        """
        Args:
            candle (dict): {
                "timestamp": datetime,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float
            }

        Returns:
            str: "BUY", "SELL", or "NONE"
        """
        pass
