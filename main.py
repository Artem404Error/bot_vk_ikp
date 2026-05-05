from utils.logger import logger
from core.exporter import ExcelExporter
from core.fsm import DialogManager
from services.vk_bot import VKBot
from config import settings
from utils.middleware import logging_middleware


def main():
    """Точка входа в приложение"""
    logger.info("Initializing bot...")
    exporter = ExcelExporter(settings.LEADS_FILE)
    fsm = DialogManager(exporter)
    bot = VKBot(fsm, exporter)

    # Добавляем мидлвары (можно расширить)
    bot.middlewares.add(logging_middleware)

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()