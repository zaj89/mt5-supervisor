from datetime import datetime

from app.logger import logger
from app.state_manager import state_manager
from app.config import config
from app.close_all import close_all_engine
from app.system_manager import system_manager

class RiskManager:

    def __init__(self):

        self.state = state_manager.load()

    def reset_day(self, current_equity):

        trading_config = config.data["trading"]

        profit_percent = trading_config["daily_profit_percent"]
        loss_percent = trading_config["daily_loss_percent"]

        profit_target = current_equity * (1 + profit_percent / 100)
        loss_limit = current_equity * (1 - loss_percent / 100)

        self.state["trading_blocked"] = False
        self.state["session_locked"] = False
        self.state["block_reason"] = None

        self.state["start_equity"] = current_equity

        self.state["daily_profit_target"] = round(profit_target, 2)
        self.state["daily_loss_limit"] = round(loss_limit, 2)

        self.state["current_day"] = datetime.now().strftime("%Y-%m-%d")

        state_manager.save(self.state)

        logger.info("New trading day initialized")

        logger.info(
            f"Start Equity={current_equity} | "
            f"TP={profit_target:.2f} | "
            f"DD={loss_limit:.2f}"
        )

    def check_new_day(self, current_equity):

        today = datetime.now().strftime("%Y-%m-%d")

        if self.state["current_day"] != today:

            self.reset_day(current_equity)

    def check_limits(self, equity):

        if self.state["trading_blocked"]:
            return

        profit_target = self.state["daily_profit_target"]
        loss_limit = self.state["daily_loss_limit"]

        if equity >= profit_target:

            self.state["trading_blocked"] = True
            self.state["block_reason"] = "daily_profit"
            self.state["session_locked"] = True

            state_manager.save(self.state)

            logger.warning(
                f"DAILY PROFIT TARGET REACHED | Equity={equity}"
            )

            close_all_engine.emergency_close_all()
            if config.data["trading"]["kill_mt5_after_limit"]:
                system_manager.kill_mt5()


        elif equity <= loss_limit:

            self.state["trading_blocked"] = True

            self.state["block_reason"] = "daily_loss"
            self.state["session_locked"] = True
            state_manager.save(self.state)

            logger.warning(

                f"DAILY LOSS LIMIT REACHED | Equity={equity}"

            )

            close_all_engine.emergency_close_all()
            if config.data["trading"]["kill_mt5_after_limit"]:
                system_manager.kill_mt5()
    def get_state(self):

        return self.state


risk_manager = RiskManager()