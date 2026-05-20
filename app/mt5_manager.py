import MetaTrader5 as mt5

from app.logger import logger


class MT5Manager:
    def is_connected(self):

        try:

            account = mt5.account_info()

            return account is not None

        except Exception:

            return False

    def reconnect(self):

        logger.warning("RECONNECTING MT5 API")

        try:

            mt5.shutdown()

        except Exception:
            pass

        result = mt5.initialize()

        if not result:

            logger.error(
                f"MT5 reconnect failed: {mt5.last_error()}"
            )

            return False

        logger.warning("MT5 RECONNECTED SUCCESSFULLY")

        return True
    def initialize(self):

        logger.info("Initializing MT5...")

        result = mt5.initialize()

        if not result:
            logger.error(f"MT5 initialize failed: {mt5.last_error()}")
            return False

        logger.info("MT5 connected successfully")

        return True

    def shutdown(self):

        mt5.shutdown()

        logger.info("MT5 shutdown")

    def get_account_info(self):

        try:

            account = mt5.account_info()

            if account is None:
                logger.error("MT5 account_info returned None")

                return None

            return account

        except Exception as error:

            logger.error(f"Account info error: {error}")

            return None

    def get_balance(self):

        account = self.get_account_info()

        if account is None:
            return None

        return account.balance

    def get_equity(self):

        account = self.get_account_info()

        if account is None:
            return None

        return account.equity

    def get_positions(self):

        positions = mt5.positions_get()

        if positions is None:
            return []

        result = []

        for position in positions:

            result.append({
                "ticket": position.ticket,
                "symbol": position.symbol,
                "type": "BUY" if position.type == 0 else "SELL",
                "volume": position.volume,
                "profit": round(position.profit, 2)
            })

        return result

    def has_open_positions(self):

        positions = mt5.positions_get()

        if positions is None:
            return False

        return len(positions) > 0


mt5_manager = MT5Manager()