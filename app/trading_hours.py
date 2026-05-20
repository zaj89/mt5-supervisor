from datetime import datetime

from app.config import config


class TradingHours:

    def is_trading_time(self):

        trading_config = config.data["trading"]

        start = trading_config["trade_start"]
        end = trading_config["trade_end"]

        now = datetime.now().strftime("%H:%M")

        return start <= now <= end

    def get_status(self):

        return {
            "trading_time": self.is_trading_time()
        }


trading_hours = TradingHours()