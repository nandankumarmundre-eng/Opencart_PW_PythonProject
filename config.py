import os
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).with_name("config.yaml")
_file_config = {}

if _CONFIG_PATH.exists():
    with _CONFIG_PATH.open(encoding="utf-8") as config_file:
        _file_config = yaml.safe_load(config_file) or {}
    if not isinstance(_file_config, dict):
        raise ValueError(f"{_CONFIG_PATH} must contain a YAML mapping")

for _key in ("email", "password"):
    _value = _file_config.get(_key)
    if _value is not None:
        if not isinstance(_value, str) or not _value.strip():
            raise ValueError(f"'{_key}' in {_CONFIG_PATH} must be a non-empty string")
        os.environ.setdefault(f"OPENCART_{_key.upper()}", _value)

class Config:
    store_url = "http://localhost/opencart/upload/"
    email = os.getenv("OPENCART_EMAIL", "")
    password = os.getenv("OPENCART_PASSWORD", "")
    invalid_email = "pavanol123@abc.com"
    invalid_password = "test@123xyz"
    product_name = "MacBook"
    product_quantity = "1"
    total_price = "$602.00"
