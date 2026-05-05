# Документация разработчика

## Архитектура
Проект построен на **конечном автомате (FSM)**. Диалог управляется классом `DialogManager`.  
Состояния: `COLLECT_FI` → `COLLECT_PHONE` → `COLLECT_TIME` → `CONFIRM` → `FINISHED`.  
Поддерживаются возражения и перезапуск.

**Компоненты:**
- `core/fsm.py` – логика диалога.
- `core/validator.py` – валидация ФИО, телефона, парсинг времени.
- `core/exporter.py` – работа с Excel (атомарная запись, бэкапы).
- `services/vk_bot.py` – интеграция с VK API, обработка команд.
- `utils/middleware.py` – мидлвары (логирование, аналитика).

## Добавление нового поля в анкету
1. Добавить текст в `config/phrases.py`.
2. Расширить модель `LeadData` в `core/models.py`.
3. Добавить состояние в `DialogState` и методы в `DialogManager`.
4. Добавить валидатор в `core/validator.py`.
5. Обновить `ExcelExporter._init_file` и метод сохранения.

## Тестирование
Установите тестовые зависимости: `pip install pytest pytest-asyncio responses`.  
Запуск: `pytest tests/`.  
Пример теста для валидатора:
```python
def test_validate_fio():
    from core.validator import validate_fio
    assert validate_fio("Иванов Иван Иванович").is_valid
    assert not validate_fio("John Doe").is_valid