import time

import MetaTrader5 as mt5

from app.logger import logger
from app.config import config

class CloseAllEngine:

    def close_all_positions(self):

        positions = mt5.positions_get()

        if positions is None:
            logger.error("Cannot get positions")
            return False

        if len(positions) == 0:
            logger.info("No open positions")
            return True

        logger.warning(f"Closing {len(positions)} positions...")

        success = True

        retry_count = config.data["risk"]["close_retry_count"]

        retry_delay = config.data["risk"]["close_retry_delay_seconds"]

        for position in positions:

            closed = False

            for attempt in range(retry_count):

                result = self.close_position(position)

                if result:
                    closed = True

                    break

                logger.warning(
                    f"Retry close attempt "
                    f"{attempt + 1}/{retry_count} "
                    f"for ticket {position.ticket}"
                )

                time.sleep(retry_delay)

            if not closed:
                logger.error(
                    f"FAILED TO CLOSE POSITION "
                    f"{position.ticket}"
                )

                success = False

            time.sleep(0.2)

        return success

    def close_position(self, position):

        symbol = position.symbol
        volume = position.volume
        ticket = position.ticket

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            logger.error(f"Cannot get tick for {symbol}")
            return False

        if position.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 999999,
            "comment": "SUPERVISOR_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            logger.error(f"Close failed for {ticket}")
            return False

        if result.retcode != mt5.TRADE_RETCODE_DONE:

            logger.error(
                f"Close failed | "
                f"Ticket={ticket} | "
                f"Retcode={result.retcode}"
            )

            return False
        time.sleep(0.5)

        if self.is_position_open(ticket):
            logger.error(
                f"Position still exists after close | "
                f"Ticket={ticket}"
            )

            return False
        logger.warning(
            f"Position closed | "
            f"Ticket={ticket} | "
            f"Symbol={symbol}"
        )

        return True

    def remove_pending_orders(self):

        orders = mt5.orders_get()

        if orders is None:
            logger.error("Cannot get pending orders")
            return False

        if len(orders) == 0:
            logger.info("No pending orders")
            return True

        logger.warning(f"Removing {len(orders)} pending orders...")

        success = True

        for order in orders:

            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
            }

            result = mt5.order_send(request)

            if result is None:
                logger.error(f"Remove failed: {order.ticket}")
                success = False
                continue

            if result.retcode != mt5.TRADE_RETCODE_DONE:

                logger.error(
                    f"Remove failed | "
                    f"Order={order.ticket} | "
                    f"Retcode={result.retcode}"
                )

                success = False
                continue

            logger.warning(
                f"Pending removed | "
                f"Order={order.ticket}"
            )

            time.sleep(0.2)

        return success

    def emergency_close_all(self):

        logger.warning("EMERGENCY CLOSE ALL STARTED")

        positions_result = self.close_all_positions()

        orders_result = self.remove_pending_orders()

        if positions_result and orders_result:

            logger.warning("EMERGENCY CLOSE ALL COMPLETED")
            return True

        logger.error("EMERGENCY CLOSE ALL PARTIAL FAILURE")

        return False

    def is_position_open(self, ticket):

        positions = mt5.positions_get()

        if positions is None:
            return False

        for position in positions:

            if position.ticket == ticket:
                return True

        return False
close_all_engine = CloseAllEngine()

if __name__ == "__main__":

    mt5.initialize()

    engine = CloseAllEngine()

    engine.emergency_close_all()

    mt5.shutdown()