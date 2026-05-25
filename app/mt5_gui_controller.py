import pyautogui
import time

from app.logger import logger


class MT5GUIController:

    def toggle_algo_trading(self):

        logger.warning(
            "Toggling Algo Trading..."
        )

        time.sleep(1)

        pyautogui.hotkey(
            'ctrl',
            'e'
        )

        logger.warning(
            "Algo Trading toggled"
        )


mt5_gui_controller = (
    MT5GUIController()
)
