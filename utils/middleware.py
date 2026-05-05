from loguru import logger
from typing import Dict, List
from datetime import datetime, timedelta


class MiddlewareChain:
    """Простая цепочка мидлваров (логирование, антиспам, аналитика)"""
    def __init__(self):
        self.middlewares: List[callable] = []

    def add(self, middleware: callable):
        self.middlewares.append(middleware)

    def process(self, user_id: int, text: str) -> bool:
        for mw in self.middlewares:
            if not mw(user_id, text):
                return False
        return True


# ==================== Антиспам-фильтр ====================

class SpamFilter:
    """Простой антиспам-фильтр: блокирует пользователя, если он отправляет
    более `max_messages` сообщений за `window_seconds` секунд."""

    def __init__(self, max_messages: int = 5, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        # user_id -> [timestamp1, timestamp2, ...]
        self._messages: Dict[int, List[float]] = {}

    def is_spam(self, user_id: int) -> bool:
        now = datetime.now().timestamp()
        window_start = now - self.window_seconds

        # Инициализируем список, если нет
        if user_id not in self._messages:
            self._messages[user_id] = []

        # Удаляем старые записи за пределами окна
        self._messages[user_id] = [
            ts for ts in self._messages[user_id] if ts > window_start
        ]

        # Проверяем, не превышен ли лимит
        if len(self._messages[user_id]) >= self.max_messages:
            return True

        # Записываем текущее сообщение
        self._messages[user_id].append(now)
        return False

    def reset(self, user_id: int):
        """Сброс счётчика для пользователя (например, при /start)"""
        self._messages.pop(user_id, None)


# ==================== Логирование ====================

def logging_middleware(user_id: int, text: str) -> bool:
    logger.info(f"Processed message from {user_id}: {text}")
    return True


# ==================== Пример: мидлвар для аналитики ====================

def analytics_middleware(user_id: int, text: str) -> bool:
    """Заглушка для аналитики — можно расширить позже."""
    logger.debug(f"Analytics: user {user_id} sent '{text}'")
    return True
