# config/loader.py

import yaml
from pathlib import Path
from typing import Any
from functools import lru_cache

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yml"


class AppConfig:
    def __init__(self, config_file: Path = CONFIG_PATH):
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        通过 key.path 支持多级访问，如 'app.port'
        """
        keys = key_path.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val


# 用 lru_cache 实现全局单例
@lru_cache()
def get_config() -> AppConfig:
    return AppConfig()
