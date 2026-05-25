from app.config import config
from app.logger import logger
from app.mt5_manager import mt5_manager
from app.preset_manager import preset_manager
from app.risk_manager import risk_manager
from app.system_manager import system_manager


class LotUpdateManager:

    def process_daily_lot_update(self):

        enabled = config.data["risk"][
            "enable_auto_lot_update"
        ]

        if not enabled:
            return

        positions = mt5_manager.get_positions()

        if positions:

            logger.warning(
                "Skipping lot update. "
                "Open positions detected."
            )

            return

        preset_path = config.data["mt5"][
            "preset_path"
        ]

        current_lot = (
            preset_manager.get_initial_lot(
                preset_path
            )
        )

        recommended_lot = (
            risk_manager
            .get_safe_recommended_lot()
        )

        logger.info(
            f"CurrentLot={current_lot} "
            f"RecommendedLot={recommended_lot}"
        )

        if current_lot == recommended_lot:
            logger.info(
                f"Lot unchanged: "
                f"{current_lot}"
            )

            return

        logger.warning(
            f"Updating lot: "
            f"{current_lot} "
            f"-> "
            f"{recommended_lot}"
        )

        updated = (
            preset_manager.update_initial_lot(
                preset_path,
                recommended_lot
            )
        )

        if not updated:

            logger.error(
                "Lot update failed"
            )

            return

        system_manager.restart_mt5()

        logger.warning(
            "Daily lot update completed"
        )


lot_update_manager = LotUpdateManager()