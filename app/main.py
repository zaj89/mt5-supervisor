import time

from app.logger import logger
from app.mt5_manager import mt5_manager
from app.config import config
from app.risk_manager import risk_manager
from app.trading_hours import trading_hours
from app.system_manager import system_manager
from app.close_all import close_all_engine
from app.performance_tracker import performance_tracker
from app.lot_update_manager import (
    lot_update_manager
)
class Supervisor:


    def __init__(self):

        self.running = True

    def start(self):

        logger.info("Starting MT5 Supervisor...")

        connected = mt5_manager.initialize()

        if not connected:
            logger.error("Cannot connect to MT5")
            return

        interval = config.data["system"]["check_interval_seconds"]

        logger.info(f"Loop interval: {interval}s")
        self.startup_cleanup()

        while self.running:

            try:
                self.loop()
                time.sleep(interval)

            except Exception as error:

                logger.exception(f"Supervisor loop error: {error}")

                time.sleep(5)

    def loop(self):
        state = risk_manager.get_state()

        if (
                not mt5_manager.is_connected()
                and not state["session_locked"]
        ):

            logger.error("MT5 API DISCONNECTED")

            reconnected = mt5_manager.reconnect()

            if not reconnected:
                logger.error("Reconnect failed")

                time.sleep(5)

                return

            logger.warning("MT5 API RESTORED")

        if (
                not system_manager.is_mt5_running()
                and not state["session_locked"]
        ):

            logger.error("MT5 NOT RUNNING")

            system_manager.start_mt5()

            connected = mt5_manager.initialize()

            if not connected:
                logger.error("MT5 reconnect failed")
                return

            logger.warning("MT5 RECONNECTED")
        balance = mt5_manager.get_balance()
        equity = mt5_manager.get_equity()

        new_day = risk_manager.check_new_day(
            equity
        )

        if new_day:
            lot_update_manager.process_daily_lot_update()
        risk_manager.check_limits(equity)
        performance_tracker.add_daily_snapshot(
            balance,
            equity
        )
        state = risk_manager.get_state()

        trading_time = trading_hours.is_trading_time()

        logger.info(
                f"Balance={balance} | "
                f"Equity={equity} | "
                f"TradingTime={trading_time} | "
                f"Blocked={state['trading_blocked']} | "
                f"Reason={state['block_reason']} | "
                f"MarketState={risk_manager.get_market_state()} | "
                f"ATR={mt5_manager.get_atr()} | "
                f"Spread={mt5_manager.get_current_spread()}"
        )

    def startup_cleanup(self):
        state = risk_manager.get_state()

        if not state["session_locked"]:
            logger.info("No cleanup needed")

            return
        logger.warning("RUNNING STARTUP CLEANUP")

        has_positions = mt5_manager.has_open_positions()

        if not has_positions:

            logger.info("No leftover positions detected")

            return

        logger.warning(
            "LEFTOVER POSITIONS DETECTED -> CLEANING"
        )

        close_all_engine.emergency_close_all()

        logger.warning("STARTUP CLEANUP COMPLETED")

supervisor = Supervisor()