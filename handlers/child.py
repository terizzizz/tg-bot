from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from database import Database
from utils.keyboards import get_child_menu
from utils.qr_generator import generate_qr_code
from config import ROLE_CHILD

router = Router()
db = Database()


@router.message(F.text == "📷 Показать QR")
async def show_qr(message: Message):
    """Показ QR-кода ребёнку"""
    # Для ребёнка нужно найти его абонементы
    # В реальном приложении здесь бы была связь между Telegram ID ребёнка и child_id в БД
    # Пока что используем упрощённый подход
    
    # Получаем все активные абонементы ребёнка (через parent_id или другой механизм)
    # Для демо покажем сообщение об ошибке
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user or user.get("role") != ROLE_CHILD:
        await message.answer("Ошибка: ваш профиль не настроен как профиль ребёнка.")
        return
    
    # Находим абонементы ребёнка
    # Здесь нужна дополнительная логика для связи Telegram ID с child_id
    await message.answer(
        "⚠️ Для показа QR-кода нужно, чтобы родитель добавил вас в систему.\n"
        "Обратитесь к родителю."
    )


@router.message(F.text == "🕒 Расписание")
async def schedule(message: Message):
    """Расписание занятий ребёнка"""
    await message.answer(
        "🕒 Вот твои занятия:\n\n"
        "Пт — 17:00\n"
        "Вс — 12:00"
    )


@router.message(F.text == "📊 Моя статистика")
async def child_statistics(message: Message):
    """Статистика ребёнка"""
    await message.answer(
        "📊 Моя статистика:\n\n"
        "Посещено: 4 / 8\n"
        "Осталось: 4\n\n"
        "Молодец! 💪"
    )


