from enum import StrEnum, auto
from typing import Dict, Optional
from loguru import logger
from core.models import LeadData
from core.validator import validate_fio, validate_phone, parse_time
from core.exporter import ExcelExporter
from config import phrases

class DialogState(StrEnum):
    START = auto()
    ASK_CONSENT = auto()
    COLLECT_FI = auto()               # ФИО пользователя
    ASK_PARENT_DATA = auto()          # Спрашиваем, хочет ли пользователь ввести данные родителей
    COLLECT_PARENT_FIO = auto()       # Ввод ФИО родителя
    COLLECT_PARENT_PHONE = auto()     # Ввод телефона родителя
    COLLECT_PHONE = auto()
    COLLECT_TIME = auto()
    CONFIRM = auto()
    FINISHED = auto()
    OBJECTION_HANDLED = auto()

class DialogManager:
    def __init__(self, exporter: ExcelExporter):
        self.exporter = exporter
        self.sessions: Dict[int, dict] = {}

    # def _handle_age(self, user_id: int, text: str) -> str:
    #     result = validate_age(text)
    #     if not result.is_valid:
    #         return result.error_message + "\n" + phrases.ASK_AGE
    #     session = self.sessions[user_id]
    #     session["data"].age = result.value
    #     logger.info(f"User {user_id} age = {result.value}")
    #     if result.value < 18:
    #         session["state"] = DialogState.ASK_PARENT_DATA
    #         logger.info(f"State changed to ASK_PARENT_DATA for user {user_id}")
    #         return phrases.ASK_PARENT_CONSENT
    #     else:
    #         session["state"] = DialogState.COLLECT_PHONE
    #         logger.info(f"Age >=18, state changed to COLLECT_PHONE")
    #         return phrases.ASK_PHONE

    def _handle_parent_consent(self, user_id: int, text: str) -> str:
        """Обрабатывает ответ на вопрос про данные родителей.
        Если пользователь вводит 'пропустить' и т.п. — пропускает.
        Иначе считает, что это и есть ФИО родителя, и переходит к телефону.
        """
        session = self.sessions[user_id]
        text_lower = text.lower().strip()
        if text_lower in ("пропустить", "нет", "не надо", "skip", "не хочу"):
            session["state"] = DialogState.COLLECT_PHONE
            logger.info(f"Parent data skipped for user {user_id}")
            return phrases.PARENT_DATA_SKIPPED + "\n" + phrases.ASK_PHONE
        else:
            # Считаем, что пользователь сразу ввёл ФИО родителя
            result = validate_fio(text)
            if not result.is_valid:
                return phrases.PARENT_FIO_INVALID + "\n" + phrases.ASK_PARENT_CONSENT
            session["data"].parent_full_name = result.value
            session["state"] = DialogState.COLLECT_PARENT_PHONE
            logger.info(f"Parent FIO saved for user {user_id}, state changed to COLLECT_PARENT_PHONE")
            return phrases.ASK_PARENT_PHONE


    def _handle_parent_fio(self, user_id: int, text: str) -> str:
        result = validate_fio(text)   # используем ту же валидацию, что и для ФИО пользователя
        if not result.is_valid:
            # Подменяем сообщение об ошибке для родителя
            return phrases.PARENT_FIO_INVALID + "\n" + phrases.ASK_PARENT_FIO
        session = self.sessions[user_id]
        session["data"].parent_full_name = result.value
        session["state"] = DialogState.COLLECT_PARENT_PHONE
        return phrases.ASK_PARENT_PHONE

    def _handle_parent_phone(self, user_id: int, text: str) -> str:
        result = validate_phone(text)   # используем существующий валидатор телефона
        if not result.is_valid:
            return phrases.PARENT_PHONE_INVALID + "\n" + phrases.ASK_PARENT_PHONE
        session = self.sessions[user_id]
        session["data"].parent_phone = result.value
        session["state"] = DialogState.COLLECT_PHONE
        return phrases.PARENT_DATA_SAVED + "\n" + phrases.ASK_PHONE

    def handle_message(self, user_id: int, text: str) -> str:
        """Обрабатывает сообщение и возвращает ответ бота"""
        logger.info(f"=== HANDLE: user {user_id}, text='{text}', current state={self.sessions.get(user_id, {}).get('state')} ===")
        # Команда /start или "начать заново"
        if text.lower() in (phrases.CMD_START, phrases.BUTTON_RESTART.lower(), "начать заново"):
            return self._reset_dialog(user_id)

        session = self.sessions.get(user_id)
        if not session:
            return self._start_dialog(user_id)

        state = session["state"]
        lead = session["data"]

        # Обработка возражений на любом этапе
        if self._is_objection(text):
            return self._handle_objection(user_id, text)

        # Продолжение после возражения "подумаю"
        if state == DialogState.OBJECTION_HANDLED and text.lower() == phrases.BUTTON_CONTINUE.lower():
            # Возвращаемся к предыдущему состоянию
            prev_state = session.get("prev_state", DialogState.COLLECT_FI)
            session["state"] = prev_state
            # Не рекурсивный вызов, а продолжение основного потока
            state = session["state"]
            lead = session["data"]

        # Обычные состояния
        if state == DialogState.ASK_CONSENT:
            return self._handle_consent(user_id, text)
        if state == DialogState.COLLECT_FI:
            return self._handle_fio(user_id, text)
        elif state == DialogState.ASK_PARENT_DATA:      # Спрашиваем про данные родителей
            return self._handle_parent_consent(user_id, text)
        elif state == DialogState.COLLECT_PARENT_FIO:
            return self._handle_parent_fio(user_id, text)
        elif state == DialogState.COLLECT_PARENT_PHONE:
            return self._handle_parent_phone(user_id, text)
        elif state == DialogState.COLLECT_PHONE:
            return self._handle_phone(user_id, text)
        elif state == DialogState.COLLECT_TIME:
            return self._handle_time(user_id, text)
        elif state == DialogState.CONFIRM:
            return self._handle_confirm(user_id, text)

    def _start_dialog(self, user_id: int) -> str:
        self.sessions[user_id] = {
            "state": DialogState.ASK_CONSENT,   # ← было COLLECT_FI
            "data": LeadData(user_id=user_id)
        }
        return phrases.ASK_CONSENT

    def _reset_dialog(self, user_id: int) -> str:
        if user_id in self.sessions:
            del self.sessions[user_id]
        return self._start_dialog(user_id)

    def _handle_fio(self, user_id: int, text: str) -> str:
        result = validate_fio(text)
        if not result.is_valid:
            return result.error_message + "\n" + phrases.ASK_FI
        session = self.sessions[user_id]
        session["data"].full_name = result.value
        session["state"] = DialogState.ASK_PARENT_DATA
        return phrases.ASK_PARENT_CONSENT

    def _handle_phone(self, user_id: int, text: str) -> str:
        result = validate_phone(text)
        if not result.is_valid:
            return result.error_message + "\n" + phrases.ASK_PHONE
        session = self.sessions[user_id]
        session["data"].phone = result.value
        session["state"] = DialogState.COLLECT_TIME
        return phrases.ASK_TIME

    def _handle_time(self, user_id: int, text: str) -> str:
        result = parse_time(text)
        if not result.is_valid:
            return result.error_message + "\n" + phrases.ASK_TIME
        session = self.sessions[user_id]
        session["data"].preferred_time = result.value
        parent_info = ""
        if session["data"].parent_full_name and session["data"].parent_phone:
            parent_info = f"Родитель: {session['data'].parent_full_name}, тел: {session['data'].parent_phone}\n"
        elif session["data"].parent_full_name:
            parent_info = f"Родитель: {session['data'].parent_full_name} (телефон не указан)\n"
        elif session["data"].parent_phone:
            parent_info = f"Родитель: телефон {session['data'].parent_phone} (ФИО не указано)\n"
        session["state"] = DialogState.CONFIRM
        return phrases.CONFIRM_MESSAGE.format(
            fio=session["data"].full_name,
            phone=session["data"].phone,
            time=session["data"].preferred_time,
            parent_info=parent_info
        )

    def _handle_confirm(self, user_id: int, text: str) -> str:
        if text.lower() in ("да", phrases.BUTTON_YES.lower()):
            lead = self.sessions[user_id]["data"]
            lead.status = "completed"
            self.exporter.save_lead(lead)
            self.sessions[user_id]["state"] = DialogState.FINISHED
            return phrases.CONFIRM_YES
        elif text.lower() in ("нет", phrases.BUTTON_NO.lower()):
            return self._reset_dialog(user_id)
        else:
            return "Пожалуйста, ответьте 'Да' или 'Нет'."

    def _is_objection(self, text: str) -> bool:
        obj_phrases = ["не сейчас", "подумаю", "не хочу оставлять телефон", "не хочу говорить номер"]
        return any(phrase in text.lower() for phrase in obj_phrases)

    def _handle_objection(self, user_id: int, text: str) -> str:
        session = self.sessions.get(user_id)
        if not session:
            return self._start_dialog(user_id)

        lead = session["data"]
        if "не сейчас" in text.lower():
            lead.status = "postponed"
            self.exporter.save_lead(lead)
            self.sessions[user_id]["state"] = DialogState.FINISHED
            return phrases.OBJECTION_NOT_NOW
        elif "подумаю" in text.lower():
            # Сохраняем текущее состояние, переходим в OBJECTION_HANDLED
            session["prev_state"] = session["state"]
            session["state"] = DialogState.OBJECTION_HANDLED
            return phrases.OBJECTION_THINK
        elif any(phrase in text.lower() for phrase in ["не хочу оставлять телефон", "не хочу говорить номер"]):
            lead.status = "rejected"
            self.exporter.save_lead(lead)
            self.sessions[user_id]["state"] = DialogState.FINISHED
            return phrases.OBJECTION_NO_PHONE
        return self.handle_message(user_id, text)  # fallback
    
    def _handle_consent(self, user_id: int, text: str) -> str:
        text_lower = text.lower().strip()
        session = self.sessions.get(user_id)
        if not session:
            return self._start_dialog(user_id)

        if any(phrase in text_lower for phrase in phrases.CONSENT_YES_PHRASES):
            session["data"].consent_given = True
            session["state"] = DialogState.COLLECT_FI   # ← было COLLECT_FIO
            return phrases.CONSENT_YES + "\n" + phrases.ASK_FI   # ← было ASK_FIO
        elif any(phrase in text_lower for phrase in phrases.CONSENT_NO_PHRASES):
            del self.sessions[user_id]
            return phrases.CONSENT_NO
        else:
            return "Пожалуйста, ответьте 'Да' (согласен) или 'Нет' (не согласен)."