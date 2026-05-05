"""
Заглушка для проверки токена VK API.

Перед использованием:
1. Скопируйте .env.example в .env
2. Заполните VK_TOKEN и VK_GROUP_ID в .env
3. Запустите: python start.py
"""
import os
from vk_api import VkApi
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("VK_TOKEN")
if not token:
    print("❌ Ошибка: VK_TOKEN не найден в .env файле!")
    print("Скопируйте .env.example в .env и заполните данные.")
    exit(1)

vk_session = VkApi(token=token)
try:
    perms = vk_session.get_api().account.getAppPermissions()
    print(f"✅ Токен активен. Права: {perms}")
    print("4096 = messages, 8192 = groups, 12288 = messages + groups")
except Exception as e:
    print(f"❌ Ошибка проверки токена: {e}")
