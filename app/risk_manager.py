from datetime import datetime

from app.logger import logger
from app.state_manager import state_manager
from app.config import config
from app.close_all import close_all_engine
from app.system_manager import system_manager
from app.preset_manager import (
    preset_manager
)
from app.mt5_gui_controller import (
    mt5_gui_controller
)
from app.trading_hours import trading_hours
from app.mt5_manager import mt5_manager

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

            return True

        return False

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
    def get_safe_recommended_lot(self):

        recommended = (
            self.get_recommended_lot()
        )

        max_auto_lot = config.data["risk"][
            "max_auto_lot"
        ]

        return min(
            recommended,
            max_auto_lot
        )

    def get_current_preset_lot(self):

        preset_path = config.data["mt5"][
            "preset_path"
        ]

        current = (
            preset_manager.get_initial_lot(
                preset_path
            )
        )

        if current is None:
            return 0.01

        return current

    def get_recommended_lot(self):

        balance = mt5_manager.get_balance()

        if balance is None:
            return 0.01

        tiers = config.data["risk"][
            "lot_tiers"
        ]

        recommended = 0.01

        for tier in tiers:

            if balance >= tier["balance"]:

                recommended = tier["lot"]

            else:

                break

        return round(recommended, 2)
    def check_spread_filter(self):

        spread = (
            mt5_manager.get_current_spread()
        )

        if spread is None:
            return

        max_spread = config.data["risk"][
            "max_spread_points"
        ]

        if spread > max_spread:
            logger.warning(
                f"Spread too high: "
                f"{spread}"
            )

            self.pause_trading(
                "high_spread"
            )

            return

        self.resume_trading()
    def get_current_preset_lot(self):

        preset_path = config.data["mt5"][
            "preset_path"
        ]

        current = (
            preset_manager.get_initial_lot(
                preset_path
            )
        )

        if current is None:
            return 0.01

        return current
    def pause_trading(
            self,
            reason
    ):

        if self.state[
            "trading_paused"
        ]:

            return

        logger.warning(
            f"Trading paused: {reason}"
        )

        mt5_gui_controller.toggle_algo_trading()

        self.state[
            "trading_paused"
        ] = True

        self.state[
            "pause_reason"
        ] = reason

        state_manager.save(
            self.state
        )
    def resume_trading(self):

        if not self.state[
            "trading_paused"
        ]:

            return

        logger.warning(
            "Trading resumed"
        )

        mt5_gui_controller.toggle_algo_trading()

        self.state[
            "trading_paused"
        ] = False

        self.state[
            "pause_reason"
        ] = ""

        state_manager.save(
            self.state
        )

    def get_market_state(self):

        atr = mt5_manager.get_atr()

        if atr is None:
            return "UNKNOWN"

        if atr < 8:
            return "CALM"

        if atr < 15:
            return "NORMAL"

        if atr < 25:
            return "VOLATILE"

        return "DANGER"
    def can_start_session(self):

        state = self.get_state()

        if state["trading_blocked"]:

            return (
                False,
                f"BLOCKED: {state['block_reason']}"
            )

        if not trading_hours.is_trading_time():

            return (
                False,
                "Waiting For Trading Hours"
            )

        market_state = (
            self.get_market_state()
        )

        if market_state == "DANGER":

            return (
                False,
                "MARKET_DANGER"
            )

        spread = (
            mt5_manager.get_current_spread()
        )

        max_spread = config.data["risk"][
            "max_start_spread"
        ]

        if (
            spread is not None
            and spread > max_spread
        ):

            return (
                False,
                "HIGH_SPREAD"
            )

        return (
            True,
            "APPROVED"
        )

    def get_system_health(self):

        issues = []

        if not mt5_manager.is_connected():
            issues.append("MT5")

        if mt5_manager.get_atr() is None:
            issues.append("ATR")

        if mt5_manager.get_current_spread() is None:
            issues.append("SPREAD")

        if not config.data["mt5"].get(
                "preset_path"
        ):
            issues.append("PRESET")

        if len(issues) == 0:
            return (
                "HEALTHY",
                []
            )

        return (
            "WARNING",
            issues
        )
risk_manager = RiskManager()