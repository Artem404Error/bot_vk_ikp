import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from loguru import logger
from config import settings, phrases
from core.fsm import DialogManager
from core.exporter import ExcelExporter
from utils.backup import schedule_daily_backup
from utils.middleware import MiddlewareChain
from vk_api.exceptions import ApiError
import requests.exceptions

class VKBot:
    def __init__(self, fsm: DialogManager, exporter: ExcelExporter):
        self.fsm = fsm
        self.exporter = exporter
        self.vk_session = vk_api.VkApi(token=settings.VK_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk_session, settings.VK_GROUP_ID)
        self.vk = self.vk_session.get_api()
        self.middlewares = MiddlewareChain()

    def _send_message(self, peer_id: int, text: str, keyboard=None):
        """Отправка сообщения с возможной клавиатурой"""
        try:
            self.vk.messages.send(
                peer_id=peer_id,
                message=text,
                random_id=0,
                keyboard=keyboard.get_keyboard() if keyboard else None
            )

        except ApiError as e:
            if e.code == 901:
                logger.warning(f"Can't send to peer {peer_id}: {e}")
                # Здесь можно отправить уведомление администратору или сохранить ID
            else:
                logger.error(f"VK API error {e.code} for peer {peer_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send message to {peer_id}: {e}")
            raise


    def _get_keyboard_for_state(self, state):
        """Генерирует клавиатуру в зависимости от состояния"""
        keyboard = VkKeyboard(one_time=False)
        if state == "ASK_CONSENT":                     # <-- новый блок
            keyboard.add_button(phrases.BUTTON_CONSENT_YES, color=VkKeyboardColor.POSITIVE)
            keyboard.add_button(phrases.BUTTON_CONSENT_NO, color=VkKeyboardColor.NEGATIVE)
        elif state in ("CONFIRM", "confirm"):
            keyboard.add_button(phrases.BUTTON_YES, color=VkKeyboardColor.POSITIVE)
            keyboard.add_button(phrases.BUTTON_NO, color=VkKeyboardColor.NEGATIVE)
        else:
            keyboard.add_button(phrases.BUTTON_RESTART, color=VkKeyboardColor.SECONDARY)
        return keyboard

    def _handle_command(self, user_id: int, text: str) -> bool:
        """Обработка команд администрирования"""
        if user_id not in settings.ADMIN_IDS:
            return False
        if text == phrases.CMD_STATUS:
            self._send_message(user_id, "✅ Бот работает и принимает сообщения.")
            return True
        elif text == phrases.CMD_EXPORT:
            path = self.exporter.export()
            self._send_message(user_id, f"Экспорт создан: {path}")
            return True
        elif text == phrases.CMD_BACKUP:
            self.exporter.backup()
            self._send_message(user_id, "Резервная копия создана.")
            return True
        elif text == phrases.CMD_STATS:
            stats = self.exporter.get_stats()
            msg = (f"📊 Статистика:\nВсего лидов: {stats['total']}\n"
               f"За сегодня: {stats['today']}\nСтатусы: {stats['statuses']}")
            self._send_message(user_id, msg)
            return True
        elif text == phrases.CMD_RELOAD:
            import importlib
            import config.phrases
            importlib.reload(config.phrases)
            # Обновляем ссылку на phrases в текущем модуле
            globals()['phrases'] = config.phrases
            self._send_message(user_id, "Конфигурация перезагружена.")
            return True
        return False

    def run(self):
        logger.info("Bot started")
        schedule_daily_backup(self.exporter)

        while True:
            try:
                for event in self.longpoll.listen():
                    try:
                        if event.type == VkBotEventType.MESSAGE_NEW and event.message:
                            user_id = event.message.from_id
                            peer_id = event.message.peer_id
                            text = event.message.text
                            logger.debug(f"Message from {user_id} in peer {peer_id}: {text}")

                            if not self.middlewares.process(user_id, text):
                                continue

                            if self._handle_command(user_id, text):
                                continue

                            response = self.fsm.handle_message(user_id, text)
                            logger.info(f"Response to user {user_id}: {response[:100]}")
                            state = self.fsm.sessions.get(user_id, {}).get("state", "")
                            keyboard = self._get_keyboard_for_state(state)
                            self._send_message(peer_id, response, keyboard)

                    except ApiError as e:
                        logger.error(f"VK API error while processing event: {e}")
                    except Exception as e:
                        logger.error(f"Error processing event: {e}", exc_info=True)

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"LongPoll connection lost: {e}. Reconnecting in 5 seconds...")
                import time
                time.sleep(5)
            except Exception as e:
                logger.error(f"Fatal error in longpoll loop: {e}", exc_info=True)
                logger.warning("Reconnecting in 10 seconds...")
                import time
                time.sleep(10)
