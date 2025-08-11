import configparser
import os
from collections import defaultdict


class Config:

    def __init__(self):
        self._config = defaultdict(str)

    def configure(
        self,
        params=None,
        ini_path=None,
        ini_section=None,
        env_use=True,
        env_prefix=None,
    ):
        if ini_path and os.path.exists(ini_path):
            self._read_ini(ini_path, section=ini_section)
        if env_use:
            self._read_env(prefix=env_prefix)
        if params:
            self._apply_params(params)

    def clear(self):
        self._config.clear()

    def _read_ini(self, ini_path, section=None):
        try:
            parser = configparser.ConfigParser()
            parser.read(ini_path)
        except Exception as e:
            print(f"Error reading INI file {ini_path}: {e}")
            return
        if not section:
            section = "DEFAULT"
        for key, value in parser.items(section):
            ckey = key.lower().replace("-", "_")
            self._config[ckey] = value

    def _read_env(self, prefix=None):
        for key in self._config:
            env_key = f"{prefix}_{key}" if prefix else str(key)
            env_key = env_key.upper().replace("-", "_")
            if env_key in os.environ:
                self._config[key] = os.environ[env_key]

    def _apply_params(self, params):
        for key, value in params.items():
            self[key] = value

    def get(self, key, default=None):
        key = key.lower().replace("-", "_")
        return self._config.get(key, default)

    def as_dict(self):
        return dict(self._config)

    def __getitem__(self, key):
        key = key.lower().replace("-", "_")
        return self._config[key]

    def __setitem__(self, key, value):
        key = key.lower().replace("-", "_")
        self._config[key] = value

    def __contains__(self, key):
        key = key.lower().replace("-", "_")
        return key in self._config


config = Config()
