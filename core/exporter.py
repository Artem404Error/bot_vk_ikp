import pandas as pd
from pathlib import Path
from filelock import FileLock
from datetime import datetime
from loguru import logger
from core.models import LeadData
from config import settings
import shutil

class ExcelExporter:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lock_path = file_path.with_suffix('.lock')
        self._init_file()

    def _init_file(self):
        """Создаёт файл с заголовками, если не существует"""
        if not self.file_path.exists():
            df = pd.DataFrame(columns=[
                "timestamp", "user_id", "full_name", "phone", 
                "preferred_time", "status", "consent_given", 
                "parent_full_name", "parent_phone"
])
            df.to_excel(self.file_path, index=False, engine='openpyxl')

    def save_lead(self, lead: LeadData):
        """Атомарная дозапись с блокировкой"""
        lock = FileLock(self.lock_path)
        with lock:
            try:
                # Читаем существующий DataFrame
                df = pd.read_excel(self.file_path, engine='openpyxl')
                # Добавляем новую строку
                new_row = pd.DataFrame([{
                    "timestamp": lead.timestamp,
                    "user_id": lead.user_id,
                    "full_name": lead.full_name,
                    "phone": lead.phone,
                    "preferred_time": lead.preferred_time,
                    "status": lead.status,
                    "consent_given": lead.consent_given,
                    "parent_full_name": lead.parent_full_name,
                    "parent_phone": lead.parent_phone
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                # Записываем обратно
                df.to_excel(self.file_path, index=False, engine='openpyxl')
                logger.info(f"Lead saved for user {lead.user_id}")
            except Exception as e:
                logger.error(f"Failed to save lead: {e}")
                raise

    def backup(self):
        """Создаёт копию файла с меткой времени"""
        if self.file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = settings.BACKUP_DIR / f"leads_backup_{timestamp}.xlsx"
            shutil.copy2(self.file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")

    def get_stats(self) -> dict:
        """Возвращает статистику по лидам"""
        if not self.file_path.exists():
            return {"total": 0, "today": 0, "statuses": {}}
        df = pd.read_excel(self.file_path, engine='openpyxl')
        total = len(df)
        today = len(df[pd.to_datetime(df['timestamp']).dt.date == datetime.now().date()])
        statuses = df['status'].value_counts().to_dict()
        return {"total": total, "today": today, "statuses": statuses}

    def export(self, target_path: Path = None):
        """Принудительный экспорт (копия)"""
        if target_path is None:
            target_path = settings.DATA_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        shutil.copy2(self.file_path, target_path)
        return target_path