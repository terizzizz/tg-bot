from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from utils.keyboards import get_partner_menu
from config import ROLE_PARTNER, STATUS_PENDING, STATUS_APPROVED, CITIES, CATEGORIES

router = Router()
db = Database()


class PartnerRegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_logo = State()
    waiting_for_schedule = State()
    waiting_for_prices = State()


@router.message(Command("partner"))
async def cmd_partner(message: Message, state: FSMContext):
    """Вход для партнёра"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await db.create_user(user_id, message.from_user.username, message.from_user.full_name, ROLE_PARTNER)
        user = await db.get_user(user_id)
    elif user.get("role") != ROLE_PARTNER:
        await db.update_user_role(user_id, ROLE_PARTNER)
    
    # Проверяем, есть ли уже центр
    center = await db.get_partner_center(user_id)
    
    if center:
        if center.get("status") == STATUS_APPROVED:
            await message.answer(
                "Добро пожаловать в панель центра!\n\n"
                "Выбери действие:",
                reply_markup=get_partner_menu()
            )
        elif center.get("status") == STATUS_PENDING:
            await message.answer("Ваш центр отправлен на модерацию. Ожидайте подтверждения.")
        else:
            await message.answer("Ваш центр был отклонён. Обратитесь в поддержку.")
    else:
        await message.answer(
            "Здравствуйте! Давайте зарегистрируем ваш центр.\n\n"
            "Название центра?"
        )
        await state.set_state(PartnerRegistrationStates.waiting_for_name)


@router.message(PartnerRegistrationStates.waiting_for_name)
async def partner_name_received(message: Message, state: FSMContext):
    """Название центра получено"""
    await state.update_data(name=message.text)
    await message.answer("Город?")
    await state.set_state(PartnerRegistrationStates.waiting_for_city)


@router.message(PartnerRegistrationStates.waiting_for_city)
async def partner_city_received(message: Message, state: FSMContext):
    """Город получен"""
    await state.update_data(city=message.text)
    await message.answer("Адрес?")
    await state.set_state(PartnerRegistrationStates.waiting_for_address)


@router.message(PartnerRegistrationStates.waiting_for_address)
async def partner_address_received(message: Message, state: FSMContext):
    """Адрес получен"""
    await state.update_data(address=message.text)
    await message.answer("Телефон?")
    await state.set_state(PartnerRegistrationStates.waiting_for_phone)


@router.message(PartnerRegistrationStates.waiting_for_phone)
async def partner_phone_received(message: Message, state: FSMContext):
    """Телефон получен"""
    await state.update_data(phone=message.text)
    await message.answer("Категория? (языки / IT / музыка / математика / ЕНТ...)")
    await state.set_state(PartnerRegistrationStates.waiting_for_category)


@router.message(PartnerRegistrationStates.waiting_for_category)
async def partner_category_received(message: Message, state: FSMContext):
    """Категория получена"""
    await state.update_data(category=message.text)
    await message.answer("Описание центра?")
    await state.set_state(PartnerRegistrationStates.waiting_for_description)


@router.message(PartnerRegistrationStates.waiting_for_description)
async def partner_description_received(message: Message, state: FSMContext):
    """Описание получено"""
    await state.update_data(description=message.text)
    await message.answer("Отправьте логотип (фото) или напишите 'пропустить':")
    await state.set_state(PartnerRegistrationStates.waiting_for_logo)


@router.message(PartnerRegistrationStates.waiting_for_logo)
async def partner_logo_received(message: Message, state: FSMContext):
    """Логотип получен"""
    logo = None
    if message.photo:
        logo = message.photo[-1].file_id
    elif message.text and message.text.lower() == "пропустить":
        pass
    else:
        await message.answer("Отправьте фото или напишите 'пропустить'")
        return
    
    await state.update_data(logo=logo)
    await message.answer("Расписание? (например: Пн-Пт 10:00-18:00)")
    await state.set_state(PartnerRegistrationStates.waiting_for_schedule)


@router.message(PartnerRegistrationStates.waiting_for_schedule)
async def partner_schedule_received(message: Message, state: FSMContext):
    """Расписание получено"""
    await state.update_data(schedule=message.text)
    await message.answer(
        "Укажите цены (в тенге, через запятую):\n"
        "4 занятия, 8 занятий, безлимит\n"
        "Например: 15000, 28000, 40000"
    )
    await state.set_state(PartnerRegistrationStates.waiting_for_prices)


@router.message(PartnerRegistrationStates.waiting_for_prices)
async def partner_prices_received(message: Message, state: FSMContext):
    """Цены получены, завершение регистрации"""
    try:
        prices = [int(p.strip()) for p in message.text.split(",")]
        if len(prices) != 3:
            raise ValueError
        
        user_id = message.from_user.id
        data = await state.get_data()
        
        # Создаём центр
        center_id = await db.create_center(user_id, {
            "name": data.get("name"),
            "city": data.get("city"),
            "address": data.get("address"),
            "phone": data.get("phone"),
            "category": data.get("category"),
            "description": data.get("description"),
            "logo": data.get("logo"),
            "status": STATUS_PENDING
        })
        
        # Создаём курс с ценами
        await db.create_course(center_id, {
            "name": f"Курс {data.get('name')}",
            "description": data.get("description"),
            "category": data.get("category"),
            "schedule": data.get("schedule"),
            "price_4": prices[0],
            "price_8": prices[1],
            "price_unlimited": prices[2]
        })
        
        await message.answer(
            "✅ Ваш центр отправлен на модерацию.\n\n"
            "Ожидайте подтверждения от администратора."
        )
        await state.clear()
    except (ValueError, IndexError):
        await message.answer(
            "Ошибка в формате цен. Введите три числа через запятую:\n"
            "15000, 28000, 40000"
        )


@router.message(F.text == "📋 Ученики")
async def partner_students(message: Message):
    """Список учеников партнёра"""
    user_id = message.from_user.id
    center = await db.get_partner_center(user_id)
    
    if not center:
        await message.answer("Центр не найден.")
        return
    
    students = await db.get_center_students(center["center_id"])
    
    if not students:
        await message.answer("У вас пока нет учеников.")
        return
    
    text = "📋 Список учеников:\n\n"
    for student in students:
        name = student.get("child_name") or student.get("full_name", "Неизвестно")
        remaining = student.get("remaining_lessons", 0)
        text += f"• {name} — осталось {remaining} занятий\n"
    
    await message.answer(text)


@router.message(F.text == "🧾 Сканировать QR")
async def scan_qr(message: Message, state: FSMContext):
    """Режим сканирования QR"""
    await message.answer(
        "🧾 Отправьте QR-код или его текст для сканирования.\n\n"
        "Внимание: В реальном приложении здесь был бы режим камеры Telegram."
    )


@router.message(F.text.startswith("SUBSCRIPTION:"))
async def qr_scanned(message: Message):
    """Обработка отсканированного QR-кода"""
    qr_text = message.text
    parts = qr_text.split(":")
    
    if len(parts) < 3:
        await message.answer("❌ Неверный формат QR-кода.")
        return
    
    qr_id = parts[1]
    subscription = await db.get_subscription_by_qr(qr_id)
    
    if not subscription:
        await message.answer("❌ Абонемент недействителен или закончился.")
        return
    
    user_id = message.from_user.id
    center = await db.get_partner_center(user_id)
    
    if not center or center["center_id"] != subscription["center_id"]:
        await message.answer("❌ Этот QR-код не принадлежит вашему центру.")
        return
    
    # Записываем посещение
    success = await db.record_visit(
        subscription["subscription_id"],
        center["center_id"]
    )
    
    if not success:
        await message.answer("❌ Ошибка при записи посещения.")
        return
    
    remaining = subscription.get("lessons_remaining", 0) - 1
    student_name = subscription.get("child_name") or subscription.get("full_name", "Ученик")
    
    await message.answer(
        f"✅ Посещение подтверждено.\n\n"
        f"Ученик: {student_name}\n"
        f"Осталось занятий: {remaining}"
    )
    
    # Отправляем уведомление родителю (если это ребёнок)
    if subscription.get("child_id"):
        parent_id = subscription.get("user_id")
        # В реальном приложении здесь бы была отправка сообщения родителю


@router.message(F.text == "📊 Аналитика")
async def partner_analytics(message: Message):
    """Аналитика для партнёра"""
    user_id = message.from_user.id
    center = await db.get_partner_center(user_id)
    
    if not center:
        await message.answer("Центр не найден.")
        return
    
    analytics = await db.get_center_analytics(center["center_id"])
    
    text = "📈 Статистика за месяц:\n\n"
    text += f"Посещений: {analytics.get('visits_count', 0)}\n"
    text += f"Продано абонементов: {analytics.get('sales_count', 0)}\n"
    text += f"Доход: {analytics.get('total_revenue', 0):,} ₸"
    
    await message.answer(text)

