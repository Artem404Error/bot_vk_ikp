import schedule
import threading
import time
from loguru import logger


def schedule_daily_backup(exporter):
    """Запускает ежесуточное резервное копирование в отдельном потоке"""

    def job():
        try:
            exporter.backup()
            logger.info("Daily backup executed successfully")
        except Exception as e:
            logger.error(f"Backup failed: {e}")

    schedule.every().day.at("03:00").do(job)

    def run_scheduler():
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(30)  # Уменьшил интервал с 60 до 30 секунд для более точного срабатывания

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logger.info("Backup scheduler started")
