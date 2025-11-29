from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import CITIES, CATEGORIES


# Главное меню для обычного пользователя
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Каталог курсов")],
            [KeyboardButton(text="🎫 Мои абонементы")],
            [KeyboardButton(text="💳 Мои платежи")],
            [KeyboardButton(text="🕒 Расписание")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🆘 Поддержка")]
        ],
        resize_keyboard=True
    )


# Меню для родителя
def get_parent_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧒 Мои дети")],
            [KeyboardButton(text="🎫 Купить абонемент")],
            [KeyboardButton(text="📅 Расписание")],
            [KeyboardButton(text="📊 Посещаемость")],
            [KeyboardButton(text="💳 Покупки")]
        ],
        resize_keyboard=True
    )


# Меню для ребёнка
def get_child_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Показать QR")],
            [KeyboardButton(text="🕒 Расписание")],
            [KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True
    )


# Меню для партнёра
def get_partner_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Ученики")],
            [KeyboardButton(text="🧾 Сканировать QR")],
            [KeyboardButton(text="🗓 Расписание")],
            [KeyboardButton(text="🎓 Курсы")],
            [KeyboardButton(text="👩‍🏫 Преподаватели")],
            [KeyboardButton(text="📊 Аналитика")],
            [KeyboardButton(text="⚙ Настройки")]
        ],
        resize_keyboard=True
    )


# Меню для админа
def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Центры")],
            [KeyboardButton(text="👥 Пользователи")],
            [KeyboardButton(text="👶 Дети / Родители")],
            [KeyboardButton(text="🎫 Абонементы")],
            [KeyboardButton(text="💳 Оплаты")],
            [KeyboardButton(text="📝 Логи посещений")],
            [KeyboardButton(text="✅ Модерация")],
            [KeyboardButton(text="📢 Рассылки")]
        ],
        resize_keyboard=True
    )


# Старт для родителя (используется в handlers)
def get_parent_start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👶 Добавить ребёнка", callback_data="parent_add_child")],
            [InlineKeyboardButton(text="⏭ Пропустить", callback_data="parent_skip")]
        ]
    )


# Клавиатура выбора параметров поиска
def get_search_params_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Город", callback_data="search_city")],
            [InlineKeyboardButton(text="📂 Категория", callback_data="search_category")],
            [InlineKeyboardButton(text="💰 Цена", callback_data="search_price")],
            [InlineKeyboardButton(text="🎂 Возраст", callback_data="search_age")],
            [InlineKeyboardButton(text="⭐ Рейтинг", callback_data="search_rating")]
        ]
    )


# Клавиатура выбора городов
def get_cities_keyboard():
    keyboard = []
    for i in range(0, len(CITIES), 2):
        row = [
            InlineKeyboardButton(text=CITIES[i], callback_data=f"city_{CITIES[i]}")
        ]
        if i + 1 < len(CITIES):
            row.append(InlineKeyboardButton(text=CITIES[i + 1], callback_data=f"city_{CITIES[i + 1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клавиатура выбора категорий
def get_categories_keyboard():
    keyboard = []
    for i in range(0, len(CATEGORIES), 2):
        row = [
            InlineKeyboardButton(text=CATEGORIES[i], callback_data=f"category_{CATEGORIES[i]}")
        ]
        if i + 1 < len(CATEGORIES):
            row.append(InlineKeyboardButton(text=CATEGORIES[i + 1], callback_data=f"category_{CATEGORIES[i + 1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клавиатура для карточки курса
def get_course_keyboard(course_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"course_detail_{course_id}")],
            [InlineKeyboardButton(text="🛒 Купить абонемент", callback_data=f"buy_course_{course_id}")]
        ]
    )


# Клавиатура для детальной информации о курсе
def get_course_detail_keyboard(course_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить абонемент", callback_data=f"buy_course_{course_id}")],
            [InlineKeyboardButton(text="💬 Посмотреть отзывы", callback_data=f"reviews_{course_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_catalog")]
        ]
    )


# Клавиатура выбора тарифа
def get_tariff_keyboard(course_id: int, price_4: int = None, price_8: int = None, price_unlimited: int = None):
    keyboard = []
    if price_4:
        keyboard.append([InlineKeyboardButton(
            text=f"4 занятия — {price_4:,}₸",
            callback_data=f"tariff_{course_id}_4"
        )])
    if price_8:
        keyboard.append([InlineKeyboardButton(
            text=f"8 занятий — {price_8:,}₸",
            callback_data=f"tariff_{course_id}_8"
        )])
    if price_unlimited:
        keyboard.append([InlineKeyboardButton(
            text=f"Безлимит — {price_unlimited:,}₸",
            callback_data=f"tariff_{course_id}_unlimited"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"course_detail_{course_id}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клавиатура оплаты
def get_payment_keyboard(subscription_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Kaspi", callback_data=f"payment_kaspi_{subscription_id}")],
            [InlineKeyboardButton(text="💳 Telegram Payments", callback_data=f"payment_telegram_{subscription_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ]
    )


# Клавиатура для абонементов
def get_subscription_keyboard(subscription_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📷 Показать QR", callback_data=f"show_qr_{subscription_id}")],
            [InlineKeyboardButton(text="🔄 Продлить", callback_data=f"extend_{subscription_id}")],
            [InlineKeyboardButton(text="📜 История", callback_data=f"history_{subscription_id}")]
        ]
    )


# Клавиатура выбора ребёнка для покупки
def get_children_keyboard(children: list):
    keyboard = []
    for child in children:
        keyboard.append([InlineKeyboardButton(
            text=f"{child['name']} ({child['age']} лет)",
            callback_data=f"select_child_{child['child_id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_parent_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клавиатура модерации
def get_moderation_keyboard(center_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_center_{center_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_center_{center_id}")]
        ]
    )


# Кнопка "Назад"
def get_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ]
    )

