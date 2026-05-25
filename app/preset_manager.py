from pathlib import Path

from app.logger import logger


class PresetManager:

    def update_initial_lot(
            self,
            preset_path,
            new_lot
    ):

        preset = Path(preset_path)

        content = preset.read_text(
            encoding="utf-16"
        )

        lines = content.splitlines()

        updated_lines = []

        changed = False

        for line in lines:

            if line.startswith("InitialLot="):

                old = line.split("=")[1]

                new_line = f"InitialLot={new_lot:.2f}"

                updated_lines.append(new_line)

                logger.warning(
                    f"InitialLot changed: "
                    f"{old} -> {new_lot:.2f}"
                )

                changed = True

            else:

                updated_lines.append(line)

        if not changed:

            logger.error(
                "InitialLot parameter not found"
            )

            return False

        preset.write_text(
            "\n".join(updated_lines),
            encoding="utf-16"
        )

        logger.warning(
            "Preset updated successfully"
        )

        return True
    def get_initial_lot(
            self,
            preset_path
    ):

        preset = Path(preset_path)

        content = preset.read_text(
            encoding="utf-16"
        )

        lines = content.splitlines()

        for line in lines:

            if line.startswith("InitialLot="):

                value = line.split("=")[1]

                return float(value)

        logger.error(
            "InitialLot parameter not found"
        )

        return None

preset_manager = PresetManager()
