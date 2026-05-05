from loguru import logger
import re
import dateparser
from datetime import datetime
from core.models import ValidationResult
from config import settings


def validate_fio(text: str) -> ValidationResult:
    """Проверка ФИ: 2 слова, кириллица, возможен дефис"""
    text = text.strip()
    words = text.split()
    if len(words) != 2:
        return ValidationResult(is_valid=False, error_message="Должно быть 2 слова")
    pattern = r'^[А-ЯЁа-яё\-]+$'
    for word in words:
        if not re.match(pattern, word):
            return ValidationResult(is_valid=False, error_message="Только буквы кириллицы и дефис")
    return ValidationResult(is_valid=True, value=text)


def validate_phone(phone: str) -> ValidationResult:
    """Принимает +7 (XXX) XXX-XX-XX или просто 10 цифр после 7/8"""
    cleaned = re.sub(r'\D', '', phone)
    if len(cleaned) == 11 and cleaned.startswith('7'):
        cleaned = '8' + cleaned[1:]
    if len(cleaned) == 10:
        cleaned = '8' + cleaned
    if len(cleaned) == 11 and cleaned.startswith('8'):
        formatted = f"+7 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:9]}-{cleaned[9:]}"
        return ValidationResult(is_valid=True, value=formatted)
    return ValidationResult(is_valid=False, error_message="Некорректный номер")


def parse_time(text: str) -> ValidationResult:
    """Парсит естественно-языковое время, возвращает строку для отображения"""
    text_lower = text.lower().strip()
    if any(phrase in text_lower for phrase in ["любое время", "не важно", "в любое", "когда удобно"]):
        return ValidationResult(is_valid=True, value="Любое удобное время")
    
    try:
        parsed = dateparser.parse(
            text,
            settings={'TIMEZONE': settings.TIMEZONE, 'RETURN_AS_TIMEZONE_AWARE': False}
        )
        if parsed and parsed > datetime.now():
            formatted = parsed.strftime("%d.%m.%Y в %H:%M")
            return ValidationResult(is_valid=True, value=formatted)
    except Exception as e:
        logger.warning(f"Failed to parse time '{text}': {e}")
    
    return ValidationResult(is_valid=False, error_message="Не удалось распознать время. Укажите, например: 'завтра после 18', 'в среду утром' или 'любое время'.")