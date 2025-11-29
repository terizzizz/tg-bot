"""
Валидаторы для проверки данных пользователей
"""
import re
from typing import Optional


def validate_age(age_str: str) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Валидация возраста
    Returns: (is_valid, age, error_message)
    """
    try:
        age = int(age_str)
        if age < 1:
            return False, None, "Возраст должен быть больше 0"
        if age > 120:
            return False, None, "Возраст должен быть меньше 120"
        return True, age, None
    except ValueError:
        return False, None, "Возраст должен быть числом"


def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
    """
    Валидация номера телефона
    Returns: (is_valid, error_message)
    """
    # Убираем все нецифровые символы
    cleaned = re.sub(r'\D', '', phone)
    
    # Проверяем длину (должно быть 10-15 цифр)
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Номер телефона должен содержать от 10 до 15 цифр"
    
    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Валидация email
    Returns: (is_valid, error_message)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Неверный формат email"
    return True, None


def validate_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Валидация имени
    Returns: (is_valid, error_message)
    """
    name = name.strip()
    
    if len(name) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    
    if len(name) > 50:
        return False, "Имя слишком длинное (максимум 50 символов)"
    
    # Проверка на недопустимые символы
    if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\s-]+$', name):
        return False, "Имя может содержать только буквы, пробелы и дефисы"
    
    return True, None


def validate_price(price_str: str) -> tuple[bool, Optional[int], Optional[str]]:
    """
    Валидация цены
    Returns: (is_valid, price, error_message)
    """
    try:
        price = int(price_str)
        if price < 0:
            return False, None, "Цена не может быть отрицательной"
        if price > 10000000:
            return False, None, "Цена слишком большая (максимум 10,000,000)"
        return True, price, None
    except ValueError:
        return False, None, "Цена должна быть числом"


def validate_text_length(text: str, min_len: int = 0, max_len: int = 5000) -> tuple[bool, Optional[str]]:
    """
    Валидация длины текста
    Returns: (is_valid, error_message)
    """
    text = text.strip()
    
    if len(text) < min_len:
        return False, f"Текст должен содержать минимум {min_len} символов"
    
    if len(text) > max_len:
        return False, f"Текст слишком длинный (максимум {max_len} символов)"
    
    return True, None


