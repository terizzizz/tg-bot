from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from utils.keyboards import (
    get_parent_menu, get_children_keyboard, get_search_params_keyboard,
    get_cities_keyboard, get_categories_keyboard, get_course_keyboard,
    get_tariff_keyboard, get_course_detail_keyboard
)
from utils.qr_generator import generate_subscription_qr
from config import ROLE_PARENT

router = Router()
db = Database()


class ParentStates(StatesGroup):
    waiting_for_child_name = State()
    waiting_for_child_age = State()
    buying_for_child = State()


@router.callback_query(F.data == "parent_add_child")
async def add_child_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления ребёнка"""
    await callback.message.edit_text("Введите имя ребёнка:")
    await state.set_state(ParentStates.waiting_for_child_name)
    await callback.answer()


@router.message(ParentStates.waiting_for_child_name)
async def child_name_received(message: Message, state: FSMContext):
    """Обработка имени ребёнка"""
    child_name = message.text
    await state.update_data(child_name=child_name)
    await state.set_state(ParentStates.waiting_for_child_age)
    await message.answer("Введите возраст:")


@router.message(ParentStates.waiting_for_child_age)
async def child_age_received(message: Message, state: FSMContext):
    """Обработка возраста ребёнка и создание записи"""
    try:
        age = int(message.text)
        if age < 1 or age > 18:
            await message.answer("Возраст должен быть от 1 до 18 лет. Попробуйте снова:")
            return
        
        data = await state.get_data()
        child_name = data.get("child_name")
        
        user_id = message.from_user.id
        child_id = await db.add_child(user_id, child_name, age)
        
        await message.answer(
            f"✅ Ребёнок добавлен!\n\n"
            f"Теперь выбери действие:",
            reply_markup=get_parent_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число для возраста:")


@router.callback_query(F.data == "parent_skip")
async def parent_skip(callback: CallbackQuery):
    """Пропустить добавление ребёнка"""
    await callback.message.edit_text(
        "👋 Добро пожаловать!\n\n"
        "Выбери действие:",
        reply_markup=None
    )
    await callback.message.answer(
        "Выбери действие:",
        reply_markup=get_parent_menu()
    )
    await callback.answer()


@router.message(F.text == "🧒 Мои дети")
async def my_children(message: Message):
    """Список детей родителя"""
    user_id = message.from_user.id
    children = await db.get_children(user_id)
    
    if not children:
        await message.answer("У вас пока нет добавленных детей.")
        return
    
    text = "🧒 Мои дети:\n\n"
    for child in children:
        text += f"• {child['name']} ({child['age']} лет)\n"
    
    await message.answer(text)


@router.message(F.text == "🎫 Купить абонемент")
async def buy_subscription_menu(message: Message, state: FSMContext):
    """Меню покупки абонемента для ребёнка"""
    user_id = message.from_user.id
    children = await db.get_children(user_id)
    
    if not children:
        await message.answer("Сначала добавьте ребёнка.")
        return
    
    await message.answer(
        "Выбери ребёнка:",
        reply_markup=get_children_keyboard(children)
    )
    await state.set_state(ParentStates.buying_for_child)


@router.callback_query(F.data.startswith("select_child_"), ParentStates.buying_for_child)
async def child_selected_for_purchase(callback: CallbackQuery, state: FSMContext):
    """Ребёнок выбран, показываем каталог"""
    child_id = int(callback.data.replace("select_child_", ""))
    await state.update_data(child_id=child_id)
    
    await callback.message.edit_text(
        "Выбери параметры поиска:",
        reply_markup=get_search_params_keyboard()
    )
    await callback.answer()


# Обработка поиска курсов для родителя (та же логика, что и для пользователя)
@router.callback_query(F.data == "search_city", ParentStates.buying_for_child)
async def parent_select_city(callback: CallbackQuery):
    """Выбор города для родителя"""
    await callback.message.edit_text(
        "🏙 Выбери город:",
        reply_markup=get_cities_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("city_"), ParentStates.buying_for_child)
async def parent_city_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города для родителя"""
    city = callback.data.replace("city_", "")
    await state.update_data(city=city)
    
    await callback.message.edit_text(
        f"Город: {city}\n\nВыбери категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"), ParentStates.buying_for_child)
async def parent_category_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории для родителя и показ курсов"""
    category = callback.data.replace("category_", "")
    data = await state.get_data()
    city = data.get("city")
    
    # Получаем курсы
    courses = await db.get_courses(city=city, category=category)
    
    if not courses:
        await callback.message.edit_text(
            "😔 Курсов не найдено. Попробуй другие параметры.",
            reply_markup=get_search_params_keyboard()
        )
        await callback.answer()
        return
    
    # Показываем первые 5 курсов
    text = f"Найдено курсов: {len(courses)}\n\n"
    for course in courses[:5]:
        center_name = course.get("center_name", "Не указано")
        price_8 = course.get("price_8", 0)
        rating = course.get("rating", 0)
        address = course.get("address", "")
        city_name = course.get("city", "")
        
        text += f"📘 Курс: {course['name']}\n"
        text += f"🏫 {center_name}\n"
        text += f"💰 Абонемент: 8 занятий — {price_8:,}₸\n"
        text += f"⭐️ Рейтинг: {rating}\n"
        text += f"📍 {city_name}, {address}\n\n"
        
        await callback.message.answer(
            text,
            reply_markup=get_course_keyboard(course["course_id"])
        )
        text = ""
    
    await callback.answer()


@router.callback_query(F.data.startswith("course_detail_"), ParentStates.buying_for_child)
async def parent_course_detail(callback: CallbackQuery):
    """Детальная информация о курсе для родителя"""
    course_id = int(callback.data.replace("course_detail_", ""))
    course = await db.get_course(course_id)
    
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return
    
    text = f"📘 {course['name']}\n\n"
    text += f"🏫 Центр: {course.get('center_name', 'Не указано')}\n"
    text += f"📍 {course.get('city', '')}, {course.get('address', '')}\n\n"
    
    if course.get("description"):
        text += f"📝 Описание:\n{course['description']}\n\n"
    
    if course.get("schedule"):
        text += f"🕒 Расписание:\n{course['schedule']}\n\n"
    
    if course.get("requirements"):
        text += f"📋 Требования:\n{course['requirements']}\n\n"
    
    if course.get("age_min") or course.get("age_max"):
        age_text = ""
        if course.get("age_min"):
            age_text += f"от {course['age_min']}"
        if course.get("age_max"):
            if age_text:
                age_text += " "
            age_text += f"до {course['age_max']}"
        text += f"🎂 Возраст: {age_text}\n\n"
    
    text += f"⭐️ Рейтинг: {course.get('rating', 0)}\n\n"
    
    prices_text = "💰 Тарифы:\n"
    if course.get("price_4"):
        prices_text += f"• 4 занятия — {course['price_4']:,}₸\n"
    if course.get("price_8"):
        prices_text += f"• 8 занятий — {course['price_8']:,}₸\n"
    if course.get("price_unlimited"):
        prices_text += f"• Безлимит — {course['price_unlimited']:,}₸\n"
    text += prices_text
    
    await callback.message.edit_text(text, reply_markup=get_course_detail_keyboard(course_id))
    await callback.answer()


@router.callback_query(F.data.startswith("buy_course_"), ParentStates.buying_for_child)
async def parent_buy_course(callback: CallbackQuery):
    """Выбор тарифа для покупки для родителя"""
    course_id = int(callback.data.replace("buy_course_", ""))
    course = await db.get_course(course_id)
    
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Выбери тариф:",
        reply_markup=get_tariff_keyboard(
            course_id,
            course.get("price_4"),
            course.get("price_8"),
            course.get("price_unlimited")
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff_"), ParentStates.buying_for_child)
async def parent_tariff_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка покупки абонемента для ребёнка"""
    parts = callback.data.split("_")
    course_id = int(parts[1])
    tariff = parts[2]
    
    data = await state.get_data()
    child_id = data.get("child_id")
    user_id = callback.from_user.id
    
    if not child_id:
        await callback.answer("Ошибка: ребёнок не выбран", show_alert=True)
        return
    
    # Получаем данные ребёнка
    child = await db.get_child(child_id)
    if not child:
        await callback.answer("Ребёнок не найден", show_alert=True)
        return
    
    # Создаём временный абонемент для платежа
    import uuid
    temp_qr_id = str(uuid.uuid4())
    subscription_id = await db.create_subscription(user_id, course_id, tariff, temp_qr_id, child_id)
    
    if not subscription_id:
        await callback.answer("Ошибка при создании абонемента", show_alert=True)
        return
    
    # Определяем цену
    price_map = {
        "4": course.get("price_4", 0),
        "8": course.get("price_8", 0),
        "unlimited": course.get("price_unlimited", 0)
    }
    price = price_map.get(tariff, 0)
    
    # Пытаемся создать платеж
    try:
        from services.payment import AirbaPayClient, PaymentService
        from config import (
            AIRBA_PAY_BASE_URL, AIRBA_PAY_USER, AIRBA_PAY_PASSWORD,
            AIRBA_PAY_TERMINAL_ID, AIRBA_PAY_COMPANY_ID, AIRBA_PAY_WEBHOOK_URL
        )
        
        # Проверяем наличие настроек платежной системы
        if AIRBA_PAY_USER and AIRBA_PAY_PASSWORD and AIRBA_PAY_TERMINAL_ID and price > 0:
            client = AirbaPayClient(
                base_url=AIRBA_PAY_BASE_URL,
                user=AIRBA_PAY_USER,
                password=AIRBA_PAY_PASSWORD,
                terminal_id=AIRBA_PAY_TERMINAL_ID,
                company_id=AIRBA_PAY_COMPANY_ID
            )
            
            payment_service = PaymentService(client, db, AIRBA_PAY_WEBHOOK_URL)
            
            user = await db.get_user(user_id)
            phone = user.get("phone", "") if user else ""
            
            payment_result = await payment_service.create_payment(
                user_id=user_id,
                subscription_id=subscription_id,
                amount=float(price),
                currency="KZT",
                description=f"Оплата абонемента для {child['name']}: {course.get('name', 'Курс')}",
                language="ru",
                phone=phone,
                email=""
            )
            
            if payment_result.get("success"):
                redirect_url = payment_result.get("redirect_url")
                if redirect_url:
                    await callback.message.answer(
                        f"💳 Оплата абонемента для {child['name']}\n\n"
                        f"Курс: {course.get('name', 'Курс')}\n"
                        f"Тариф: {tariff} занятий\n"
                        f"Сумма: {price} ₸\n\n"
                        f"Перейдите по ссылке для оплаты:",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💳 Оплатить", url=redirect_url)],
                            [InlineKeyboardButton(text="✅ Проверить платеж", callback_data=f"check_payment_{payment_result.get('payment_id')}")],
                            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_payment_{subscription_id}")]
                        ])
                    )
                    await callback.answer()
                    await state.update_data(
                        subscription_id=subscription_id,
                        payment_id=payment_result.get("payment_id")
                    )
                    return
    except Exception as e:
        # Если платежная система не работает, создаём абонемент без оплаты
        pass
    
    # Если платежная система не настроена или цена = 0, создаём абонемент сразу
    qr_id, qr_image = generate_subscription_qr(user_id, subscription_id, child_id)
    
    # Обновляем QR-код в базе данных
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as db_conn:
        await db_conn.execute(
            "UPDATE subscriptions SET qr_code = ? WHERE subscription_id = ?",
            (qr_id, subscription_id)
        )
        await db_conn.commit()
    
    # Отправляем родителю уведомление
    await callback.message.answer(
        f"🎉 Вы купили абонемент для {child['name']}!\n\n"
        "QR-код для посещений:"
    )
    
    try:
        qr_bytes = qr_image.getvalue()
        await callback.message.answer_photo(
            photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
            caption=f"QR-код для {child['name']}"
        )
    except Exception:
        await callback.message.answer(
            f"QR-код создан!\nКод: {qr_id}\n\n"
            f"Установите Pillow для отображения QR-кода как изображения."
        )
    
    await callback.answer()
    await state.clear()


@router.message(F.text == "📊 Посещаемость")
async def children_attendance(message: Message):
    """Статистика посещаемости детей"""
    user_id = message.from_user.id
    children = await db.get_children(user_id)
    
    if not children:
        await message.answer("У вас пока нет добавленных детей.")
        return
    
    for child in children:
        stats = await db.get_visit_stats(user_id, child["child_id"])
        visits = stats.get("visits_count", 0)
        total = stats.get("total_lessons", 0)
        remaining = stats.get("remaining_lessons", 0)
        missed = total - visits - remaining if total > 0 else 0
        
        text = f"📊 Статистика {child['name']}:\n\n"
        text += f"Посещено: {visits} / {total}\n"
        text += f"Пропусков: {missed}\n"
        if remaining > 0:
            text += f"Осталось: {remaining} занятий"
        
        await message.answer(text)

