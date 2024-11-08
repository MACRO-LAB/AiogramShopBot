import json
from enum import Enum

import config


class BotEntity(Enum):
    USER = 1
    ADMIN = 2
    COMMON = 3


class Localizator:
    localization_filename = f"./l10n/{config.BOT_LANGUAGE}.json"

    @staticmethod
    def get_text(entity: BotEntity, key: str) -> str:
        with open(Localizator.localization_filename, "r", encoding="UTF-8") as f:
            if entity == BotEntity.ADMIN:
                return json.loads(f.read())["admin"][key]
            elif entity == BotEntity.USER:
                return json.loads(f.read())["user"][key]
            else:
                return json.loads(f.read())["common"][key]
