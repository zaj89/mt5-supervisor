import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

STATE_PATH = BASE_DIR / "state" / "state.json"


class StateManager:

    def load(self):

        with open(STATE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, state):

        with open(STATE_PATH, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)


state_manager = StateManager()