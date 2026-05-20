import json
from datetime import datetime
from pathlib import Path
from app.logger import logger


BASE_DIR = Path(__file__).resolve().parent.parent

PERFORMANCE_PATH = (
    BASE_DIR / "state" / "performance.json"
)


class PerformanceTracker:

    def load(self):

        with open(
            PERFORMANCE_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    def save(self, data):

        with open(
            PERFORMANCE_PATH,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(data, file, indent=2)

    def add_daily_snapshot(
            self,
            balance,
            equity
    ):

        data = self.load()

        today = datetime.now().strftime("%Y-%m-%d")

        for item in data:

            if item["date"] == today:

                return

        deposit = data[0]["deposit"] if data else balance

        target_curve = round(
            deposit * (1.01 ** len(data)),
            2
        )

        snapshot = {
            "date": today,
            "balance": round(balance, 2),
            "equity": round(equity, 2),
            "deposit": round(deposit, 2),
            "target_curve": target_curve
        }

        data.append(snapshot)

        self.save(data)

        logger.warning(
            f"Performance snapshot saved: {snapshot}"
        )

    def get_performance_data(self):

        return self.load()


performance_tracker = PerformanceTracker()