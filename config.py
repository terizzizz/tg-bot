import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]

# Настройки AirbaPay
AIRBA_PAY_BASE_URL = os.getenv("AIRBA_PAY_BASE_URL", "https://ps.airbapay.kz/acquiring-api")
AIRBA_PAY_USER = os.getenv("AIRBA_PAY_USER", "")
AIRBA_PAY_PASSWORD = os.getenv("AIRBA_PAY_PASSWORD", "")
AIRBA_PAY_TERMINAL_ID = os.getenv("AIRBA_PAY_TERMINAL_ID", "")
AIRBA_PAY_COMPANY_ID = os.getenv("AIRBA_PAY_COMPANY_ID", "230140022645")
AIRBA_PAY_WEBHOOK_URL = os.getenv("AIRBA_PAY_WEBHOOK_URL", "")

# Роли пользователей
ROLE_USER = "user"
ROLE_PARENT = "parent"
ROLE_CHILD = "child"
ROLE_PARTNER = "partner"
ROLE_ADMIN = "admin"

# Статусы
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

# Категории курсов
CATEGORIES = [
    "Языки",
    "IT",
    "Музыка",
    "Математика",
    "ЕНТ",
    "Искусство",
    "Спорт",
    "Другое"
]

# Города
CITIES = [
    "Алматы",
    "Астана",
    "Шымкент",
    "Актау",
    "Актобе",
    "Атырау",
    "Караганда",
    "Костанай",
    "Кызылорда",
    "Павлодар",
    "Петропавл",
    "Тараз",
    "Уральск",
    "Усть-Каменогорск",
    "Другое"
]


