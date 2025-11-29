# ...existing code...
# Регистрация роутеров
dp.include_router(common.router)
dp.include_router(user.router)
dp.include_router(parent.router)
dp.include_router(child.router)
dp.include_router(partner.router)
dp.include_router(admin.router)

# Собираем тексты кнопок ReplyKeyboard, чтобы игнорировать их нажатия
menu_texts = set()
try:
    from utils.keyboards import (
        get_main_menu, get_parent_menu, get_child_menu,
        get_partner_menu, get_admin_menu
    )

    def _extract_reply_texts(markup):
        texts = set()
        if not markup:
            return texts
        kb = getattr(markup, "keyboard", None)  # ReplyKeyboardMarkup.keyboard -> list[list[KeyboardButton]]
        if kb:
            for row in kb:
                for btn in row:
                    t = getattr(btn, "text", None)
                    if t:
                        texts.add(t.strip())
        return texts

    for fn in (get_main_menu, get_parent_menu, get_child_menu, get_partner_menu, get_admin_menu):
        try:
            markup = fn()
            menu_texts.update(_extract_reply_texts(markup))
        except Exception:
            # Игнорируем ошибки при построении клавиатур
            pass
except Exception:
    menu_texts = set()

# Обработчик неизвестных сообщений (должен быть последним)
from aiogram import F
from aiogram.types import Message

@dp.message(F.text & ~F.text.startswith('/'))
async def unknown_message_handler(message: Message):
    # Если текст совпадает с кнопкой ReplyKeyboard — считаем, что это нажатие кнопки и игнорируем
    text = (message.text or "").strip()
    if text and text in menu_texts:
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if user:
        role = user.get("role", "user")
        if role == "parent":
            from utils.keyboards import get_parent_menu
            await message.answer(
                "Используй кнопки меню для навигации.\n\n"
                "Или отправь /start для начала работы.",
                reply_markup=get_parent_menu()
            )
        elif role == "child":
            from utils.keyboards import get_child_menu
            await message.answer(
                "Используй кнопки меню для навигации.\n\n"
                "Или отправь /start для начала работы.",
                reply_markup=get_child_menu()
            )
        else:
            from utils.keyboards import get_main_menu
            await message.answer(
                "Используй кнопки меню для навигации.\n\n"
                "Или отправь /start для начала работы.",
                reply_markup=get_main_menu()
            )
    else:
        await message.answer(
            "👋 Привет! Отправь /start для начала работы."
        )
# ...existing code...