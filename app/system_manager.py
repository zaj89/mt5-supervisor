import subprocess
import psutil
import subprocess
import time

from app.logger import logger


class SystemManager:

    def kill_mt5(self):

        logger.warning("KILLING MT5 TERMINAL")

        try:

            subprocess.run(
                ["taskkill", "/F", "/IM", "terminal64.exe"],
                check=True,
                capture_output=True
            )

            logger.warning("MT5 TERMINATED")

            return True

        except Exception as error:

            logger.error(f"MT5 kill failed: {error}")

            return False
    def is_mt5_running(self):

        for process in psutil.process_iter(["name"]):

            try:

                if process.info["name"] == "terminal64.exe":
                    return True

            except Exception:
                continue

        return False

    def start_mt5(self):

        from app.config import config

        mt5_path = config.data["mt5"]["path"]

        logger.warning("STARTING MT5 TERMINAL")

        try:

            subprocess.Popen(mt5_path)

            time.sleep(5)

            logger.warning("MT5 STARTED")

            return True

        except Exception as error:

            logger.error(f"MT5 start failed: {error}")

            return False

system_manager = SystemManager()
if __name__ == "__main__":

    manager = SystemManager()

    manager.start_mt5()