"""
Configuration management for Food Court System
Supports both config.ini file and environment variables (Docker)
Environment variables take precedence over config.ini
"""
import configparser
import os
from pathlib import Path

# Get the directory where config.ini is located
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.ini"

config = configparser.ConfigParser()
if CONFIG_FILE.exists():
    config.read(CONFIG_FILE)

# Helper function to get config with env var fallback
def get_config(section, key, fallback=None, env_var=None, env_type=str):
    """Get config value from environment variable first, then config.ini"""
    # Check environment variable first (Docker)
    if env_var and env_var in os.environ:
        value = os.environ[env_var]
        if env_type == int:
            return int(value)
        elif env_type == float:
            return float(value)
        elif env_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        return value
    
    # Fall back to config.ini
    if config.has_section(section):
        if env_type == int:
            return config.getint(section, key, fallback=fallback)
        elif env_type == float:
            return config.getfloat(section, key, fallback=fallback)
        elif env_type == bool:
            return config.getboolean(section, key, fallback=fallback)
        return config.get(section, key, fallback=fallback)
    
    return fallback

# Database Configuration (environment variables take precedence)
DB_HOST = get_config("DATABASE", "DB_HOST", fallback="localhost", env_var="DB_HOST")
DB_PORT = get_config("DATABASE", "DB_PORT", fallback=3306, env_var="DB_PORT", env_type=int)
DB_NAME = get_config("DATABASE", "DB_NAME", fallback="maket_place_system", env_var="DB_NAME")
DB_USER = get_config("DATABASE", "DB_USER", fallback="root", env_var="DB_USER")
DB_PASSWORD = get_config("DATABASE", "DB_PASSWORD", fallback="123456", env_var="DB_PASSWORD")

# Backend Configuration
BACKEND_URL = get_config("BACKEND", "BACKEND_URL", fallback="http://localhost:8000", env_var="BACKEND_URL")
SECRET_KEY = get_config("BACKEND", "SECRET_KEY", fallback="your-secret-key-here", env_var="SECRET_KEY")
DEBUG = get_config("BACKEND", "DEBUG", fallback=True, env_var="DEBUG", env_type=bool)

# E-Money Configuration
HAS_E_MONEY_LICENSE = get_config("E_MONEY", "HAS_E_MONEY_LICENSE", fallback=False, env_var="HAS_E_MONEY_LICENSE", env_type=bool)
AUTO_REFUND_ENABLED = get_config("E_MONEY", "AUTO_REFUND_ENABLED", fallback=True, env_var="AUTO_REFUND_ENABLED", env_type=bool)
REFUND_NOTIFICATION_TIME = get_config("E_MONEY", "REFUND_NOTIFICATION_TIME", fallback="23:00", env_var="REFUND_NOTIFICATION_TIME")
DAILY_BALANCE_RESET = get_config("E_MONEY", "DAILY_BALANCE_RESET", fallback=True, env_var="DAILY_BALANCE_RESET", env_type=bool)

# Crypto Configuration
BLOCKCHAIN_EXPLORER_API = get_config("CRYPTO", "BLOCKCHAIN_EXPLORER_API", fallback="https://api.blockchain.info", env_var="BLOCKCHAIN_EXPLORER_API")
TRANSACTION_FEE = get_config("CRYPTO", "TRANSACTION_FEE", fallback=5.00, env_var="TRANSACTION_FEE", env_type=float)
MONTHLY_FLAT_FEE = get_config("CRYPTO", "MONTHLY_FLAT_FEE", fallback=500.00, env_var="MONTHLY_FLAT_FEE", env_type=float)
CRYPTO_ENABLED = get_config("CRYPTO", "ENABLED", fallback=True, env_var="CRYPTO_ENABLED", env_type=bool)

# Tax Configuration
WHT_RATE = get_config("TAX", "WHT_RATE", fallback=0.03, env_var="WHT_RATE", env_type=float)
VAT_RATE = get_config("TAX", "VAT_RATE", fallback=0.07, env_var="VAT_RATE", env_type=float)
TAX_ID = get_config("TAX", "TAX_ID", fallback="", env_var="TAX_ID")
COMPANY_NAME = get_config("TAX", "COMPANY_NAME", fallback="", env_var="COMPANY_NAME")

# Payment Configuration
PROMPTPAY_ENABLED = get_config("PAYMENT", "PROMPTPAY_ENABLED", fallback=True, env_var="PROMPTPAY_ENABLED", env_type=bool)
PROMPTPAY_API_URL = get_config("PAYMENT", "PROMPTPAY_API_URL", fallback="", env_var="PROMPTPAY_API_URL")

# Notification Configuration
LINE_OA_CHANNEL_ACCESS_TOKEN = get_config("NOTIFICATION", "LINE_OA_CHANNEL_ACCESS_TOKEN", fallback="", env_var="LINE_OA_CHANNEL_ACCESS_TOKEN")
LINE_OA_CHANNEL_SECRET = get_config("NOTIFICATION", "LINE_OA_CHANNEL_SECRET", fallback="", env_var="LINE_OA_CHANNEL_SECRET")
PUSH_NOTIFICATION_ENABLED = get_config("NOTIFICATION", "PUSH_NOTIFICATION_ENABLED", fallback=True, env_var="PUSH_NOTIFICATION_ENABLED", env_type=bool)

# Database URL - MariaDB/MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

