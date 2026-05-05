import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

VK_GROUP_ID = int(os.getenv("VK_GROUP_ID"))
VK_TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
LEADS_FILE = Path(os.getenv("LEADS_FILE", DATA_DIR / "leads.xlsx"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", DATA_DIR / "backups"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Создаём директории
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# Настройки валидации
PHONE_MASK = "+7 (___) ___-__-__"
PHONE_LENGTH = 11  # цифр после +7