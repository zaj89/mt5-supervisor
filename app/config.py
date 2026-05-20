from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"


class Config:

    def __init__(self):
        self.data = self.load()

    def load(self):

        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def reload(self):
        self.data = self.load()


config = Config()