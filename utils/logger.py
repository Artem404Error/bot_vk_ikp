from loguru import logger
import sys
from config import settings

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}",
    level=settings.LOG_LEVEL
)
logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="30 days",
    format="{time} | {level} | {message}",
    level="DEBUG"
)