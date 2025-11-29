from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import Database
from utils.keyboards import get_admin_menu, get_moderation_keyboard
from config import ROLE_ADMIN, STATUS_APPROVED, STATUS_REJECTED, ADMIN_IDS

router = Router()
db = Database()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Вход в админ-панель"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    # Обновляем роль пользователя
    await db.update_user_role(user_id, ROLE_ADMIN)
    
    await message.answer(
        "🔐 Админ-панель:\n\n"
        "Выбери действие:",
        reply_markup=get_admin_menu()
    )


@router.message(F.text == "✅ Модерация")
async def moderation_menu(message: Message):
    """Меню модерации"""
    if not is_admin(message.from_user.id):
        return
    
    pending_centers = await db.get_pending_centers()
    
    if not pending_centers:
        await message.answer("Нет новых центров на модерации.")
        return
    
    text = "📋 Новые центры:\n\n"
    for center in pending_centers[:10]:  # Показываем первые 10
        text += f"• {center['name']} (ID: {center['center_id']})\n"
        text += f"  Город: {center.get('city', 'Не указан')}\n"
        text += f"  Категория: {center.get('category', 'Не указана')}\n\n"
    
    await message.answer(text)


@router.callback_query(F.data.startswith("approve_center_"))
async def approve_center(callback: CallbackQuery):
    """Одобрение центра"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    center_id = int(callback.data.replace("approve_center_", ""))
    await db.update_center_status(center_id, STATUS_APPROVED)
    
    await callback.message.edit_text(
        f"✅ Центр #{center_id} одобрен!"
    )
    
    # В реальном приложении здесь бы было отправка уведомления партнёру
    await callback.answer()


@router.callback_query(F.data.startswith("reject_center_"))
async def reject_center(callback: CallbackQuery):
    """Отклонение центра"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    center_id = int(callback.data.replace("reject_center_", ""))
    await db.update_center_status(center_id, STATUS_REJECTED)
    
    await callback.message.edit_text(
        f"❌ Центр #{center_id} отклонён!"
    )
    
    # В реальном приложении здесь бы было отправка уведомления партнёру
    await callback.answer()


@router.message(F.text == "🏢 Центры")
async def admin_centers(message: Message):
    """Управление центрами"""
    if not is_admin(message.from_user.id):
        return
    
    # Получаем все центры
    centers = await db.get_centers()
    
    text = f"🏢 Всего центров: {len(centers)}\n\n"
    for center in centers[:20]:  # Показываем первые 20
        status_emoji = "✅" if center.get("status") == STATUS_APPROVED else "⏳" if center.get("status") == "pending" else "❌"
        text += f"{status_emoji} {center['name']} ({center.get('city', 'N/A')})\n"
    
    await message.answer(text)


@router.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    """Управление пользователями"""
    if not is_admin(message.from_user.id):
        return
    
    users = await db.get_all_users()
    
    text = f"👥 Всего пользователей: {len(users)}\n\n"
    
    # Подсчёт по ролям
    roles_count = {}
    for user in users:
        role = user.get("role", "user")
        roles_count[role] = roles_count.get(role, 0) + 1
    
    for role, count in roles_count.items():
        text += f"{role}: {count}\n"
    
    await message.answer(text)


@router.message(F.text == "🎫 Абонементы")
async def admin_subscriptions(message: Message):
    """Управление абонементами"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎫 Управление абонементами\n\n"
        "Функция в разработке."
    )


@router.message(F.text == "💳 Оплаты")
async def admin_payments(message: Message):
    """Управление платежами"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💳 Управление платежами\n\n"
        "Функция в разработке."
    )


@router.message(F.text == "📝 Логи посещений")
async def admin_visits(message: Message):
    """Логи посещений"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📝 Логи посещений\n\n"
        "Функция в разработке."
    )


@router.message(F.text == "📢 Рассылки")
async def admin_broadcast(message: Message):
    """Рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📢 Рассылки\n\n"
        "Функция в разработке."
    )


