"""
Утилиты для пагинации
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Any, Callable


def create_pagination_keyboard(
    items: List[Any],
    page: int,
    items_per_page: int,
    callback_prefix: str,
    item_formatter: Callable[[Any], str] = None,
    additional_buttons: List[List[InlineKeyboardButton]] = None
) -> tuple[List[Any], InlineKeyboardMarkup]:
    """
    Создаёт пагинацию для списка элементов
    
    Args:
        items: Список элементов для отображения
        page: Текущая страница (начиная с 0)
        items_per_page: Количество элементов на странице
        callback_prefix: Префикс для callback data (например, "course_page")
        item_formatter: Функция для форматирования элемента в текст
        additional_buttons: Дополнительные кнопки для добавления
    
    Returns:
        Tuple (items_on_page, keyboard)
    """
    total_pages = (len(items) + items_per_page - 1) // items_per_page if items else 1
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    items_on_page = items[start_idx:end_idx]
    
    keyboard = []
    
    # Кнопки пагинации
    pagination_buttons = []
    
    if total_pages > 1:
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"{callback_prefix}_page_{page - 1}"
                )
            )
        
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="page_info"
            )
        )
        
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="Вперёд ➡️",
                    callback_data=f"{callback_prefix}_page_{page + 1}"
                )
            )
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    # Дополнительные кнопки
    if additional_buttons:
        keyboard.extend(additional_buttons)
    
    return items_on_page, InlineKeyboardMarkup(inline_keyboard=keyboard)


def paginate_courses(courses: List[dict], page: int = 0, per_page: int = 5):
    """
    Пагинация курсов с форматированием
    """
    def format_course(course: dict) -> str:
        center_name = course.get("center_name", "Не указано")
        price_8 = course.get("price_8", 0)
        rating = course.get("rating", 0)
        address = course.get("address", "")
        city = course.get("city", "")
        
        text = f"📘 Курс: {course['name']}\n"
        text += f"🏫 {center_name}\n"
        text += f"💰 Абонемент: 8 занятий — {price_8:,}₸\n"
        text += f"⭐️ Рейтинг: {rating}\n"
        text += f"📍 {city}, {address}\n"
        return text
    
    items, keyboard = create_pagination_keyboard(
        items=courses,
        page=page,
        items_per_page=per_page,
        callback_prefix="courses",
        item_formatter=format_course
    )
    
    return items, keyboard


