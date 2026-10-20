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
    store_url = os.getenv("OPENCART_STORE_URL") or "http://localhost/opencart/upload/"
    practice_url = os.getenv("PLAYWRIGHT_BASE_URL") or "https://testautomationpractice.blogspot.com/"
    market_symbols = os.getenv(
        "MARKET_SYMBOLS",
        "NSE:NIFTY,DELTAIN:BTCUSD.P,MCX:NATURALGASM2026,MCX:CRUDEOILX2026",
    )
    market_report_email = os.getenv(
        "MARKET_REPORT_EMAIL",
        "nandankumarmundre@gmail.com",
    )
    market_smtp_host = os.getenv("MARKET_SMTP_HOST", "smtp.gmail.com")
    market_smtp_port = int(os.getenv("MARKET_SMTP_PORT", "587"))
    market_smtp_username = os.getenv("MARKET_SMTP_USERNAME", "")
    market_smtp_password = os.getenv("MARKET_SMTP_PASSWORD", "")
    email = os.getenv("OPENCART_EMAIL", "")
    password = os.getenv("OPENCART_PASSWORD", "")
    invalid_email = "pavanol123@abc.com"
    invalid_password = "test@123xyz"
    product_name = "MacBook"
    product_quantity = "1"
    total_price = "$602.00"
