import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from utils.keyboards import (
    get_main_menu, get_search_params_keyboard, get_cities_keyboard,
    get_categories_keyboard, get_course_keyboard, get_course_detail_keyboard,
    get_tariff_keyboard, get_payment_keyboard, get_subscription_keyboard
)
from utils.qr_generator import generate_subscription_qr
from config import ROLE_USER

logger = logging.getLogger(__name__)

router = Router()
db = Database()


class SearchStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_category = State()


@router.message(F.text == "📚 Каталог курсов")
async def catalog_menu(message: Message):
    """Показывает меню поиска курсов"""
    await message.answer(
        "Выбери параметры поиска:",
        reply_markup=get_search_params_keyboard()
    )


@router.callback_query(F.data == "search_city")
async def select_city(callback: CallbackQuery):
    """Выбор города"""
    await callback.message.edit_text(
        "🏙 Выбери город:",
        reply_markup=get_cities_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("city_"))
async def city_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города"""
    city = callback.data.replace("city_", "")
    await state.update_data(city=city)
    
    await callback.message.edit_text(
        f"Город: {city}\n\nВыбери категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def category_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории и показ курсов"""
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
    await state.clear()


@router.callback_query(F.data.startswith("course_detail_"))
async def course_detail(callback: CallbackQuery):
    """Детальная информация о курсе"""
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


@router.callback_query(F.data.startswith("buy_course_"))
async def buy_course(callback: CallbackQuery):
    """Выбор тарифа для покупки"""
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


@router.callback_query(F.data.startswith("tariff_"))
async def tariff_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора тарифа"""
    parts = callback.data.split("_")
    course_id = int(parts[1])
    tariff = parts[2]
    
    course = await db.get_course(course_id)
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return
    
    # Определяем цену
    price_map = {
        "4": course.get("price_4", 0),
        "8": course.get("price_8", 0),
        "unlimited": course.get("price_unlimited", 0)
    }
    price = price_map.get(tariff, 0)
    
    if price < 0:
        await callback.answer("Ошибка: неверная цена", show_alert=True)
        return
    
    # Сохраняем данные покупки
    user_id = callback.from_user.id
    await state.update_data(
        course_id=course_id,
        tariff=tariff,
        price=price
    )
    
    # Создаём временный абонемент для платежа
    import uuid
    temp_qr_id = str(uuid.uuid4())
    subscription_id = await db.create_subscription(user_id, course_id, tariff, temp_qr_id)
    
    if not subscription_id:
        await callback.answer("Ошибка при создании абонемента", show_alert=True)
        return
    
    # Инициализируем платежный сервис
    try:
        from services.payment import AirbaPayClient, PaymentService
        from config import (
            AIRBA_PAY_BASE_URL, AIRBA_PAY_USER, AIRBA_PAY_PASSWORD,
            AIRBA_PAY_TERMINAL_ID, AIRBA_PAY_COMPANY_ID, AIRBA_PAY_WEBHOOK_URL
        )
        
        # Проверяем наличие настроек
        if not AIRBA_PAY_USER or not AIRBA_PAY_PASSWORD or not AIRBA_PAY_TERMINAL_ID:
            # Если платежная система не настроена, создаём абонемент без оплаты
            qr_id, qr_image = generate_subscription_qr(user_id, subscription_id)
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as db_conn:
                await db_conn.execute(
                    "UPDATE subscriptions SET qr_code = ? WHERE subscription_id = ?",
                    (qr_id, subscription_id)
                )
                await db_conn.commit()
            
            await callback.message.answer(
                "🎉 Абонемент активирован!\n\n"
                "Вот твой QR-код для посещений 👇"
            )
            
            try:
                qr_bytes = qr_image.getvalue()
                await callback.message.answer_photo(
                    photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
                    caption="Твой QR-код для посещений"
                )
            except Exception:
                await callback.message.answer(
                    f"QR-код создан!\nКод: {qr_id}\n\n"
                    f"Установите Pillow для отображения QR-кода как изображения."
                )
            await callback.answer()
            await state.clear()
            return
        
        # Создаём платеж
        client = AirbaPayClient(
            base_url=AIRBA_PAY_BASE_URL,
            user=AIRBA_PAY_USER,
            password=AIRBA_PAY_PASSWORD,
            terminal_id=AIRBA_PAY_TERMINAL_ID,
            company_id=AIRBA_PAY_COMPANY_ID
        )
        
        payment_service = PaymentService(client, db, AIRBA_PAY_WEBHOOK_URL)
        
        # Получаем данные пользователя
        user = await db.get_user(user_id)
        phone = user.get("phone", "") if user else ""
        email = ""  # У пользователя может не быть email
        
        payment_result = await payment_service.create_payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=float(price),
            currency="KZT",
            description=f"Оплата абонемента: {course.get('name', 'Курс')}",
            language="ru",
            phone=phone,
            email=email
        )
        
        if not payment_result.get("success"):
            error_msg = payment_result.get("error", "Ошибка при создании платежа")
            await callback.message.answer(
                f"❌ Ошибка при создании платежа:\n{error_msg}\n\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            await callback.answer()
            return
        
        # Сохраняем payment_id в state для отслеживания
        await state.update_data(
            subscription_id=subscription_id,
            payment_id=payment_result.get("payment_id")
        )
        
        redirect_url = payment_result.get("redirect_url")
        
        if redirect_url:
            from utils.keyboards import get_payment_keyboard
            await callback.message.answer(
                f"💳 Оплата абонемента\n\n"
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
        else:
            await callback.message.answer(
                "⚠️ Ссылка на оплату не получена. Обратитесь в поддержку."
            )
        
    except ImportError:
        # Если платежный сервис не настроен, создаём абонемент без оплаты
        qr_id, qr_image = generate_subscription_qr(user_id, subscription_id)
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as db_conn:
            await db_conn.execute(
                "UPDATE subscriptions SET qr_code = ? WHERE subscription_id = ?",
                (qr_id, subscription_id)
            )
            await db_conn.commit()
        
        await callback.message.answer(
            "🎉 Абонемент активирован!\n\n"
            "Вот твой QR-код для посещений 👇"
        )
        
        try:
            qr_bytes = qr_image.getvalue()
            await callback.message.answer_photo(
                photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
                caption="Твой QR-код для посещений"
            )
        except Exception:
            await callback.message.answer(
                f"QR-код создан!\nКод: {qr_id}\n\n"
                f"Установите Pillow для отображения QR-кода как изображения."
            )
        await state.clear()
    
    await callback.answer()


@router.message(F.text == "🎫 Мои абонементы")
async def my_subscriptions(message: Message):
    """Показ абонементов пользователя"""
    user_id = message.from_user.id
    subscriptions = await db.get_user_subscriptions(user_id)
    
    if not subscriptions:
        await message.answer("У тебя пока нет абонементов.")
        return
    
    for sub in subscriptions:
        remaining = sub.get("lessons_remaining", 0)
        course_name = sub.get("course_name", "Неизвестный курс")
        
        text = f"🔹 {course_name} — осталось {remaining} занятий"
        await message.answer(text, reply_markup=get_subscription_keyboard(sub["subscription_id"]))


@router.callback_query(F.data.startswith("show_qr_"))
async def show_qr(callback: CallbackQuery):
    """Показ QR-кода"""
    subscription_id = int(callback.data.replace("show_qr_", ""))
    
    # Получаем данные абонемента
    subscriptions = await db.get_user_subscriptions(callback.from_user.id)
    subscription = next((s for s in subscriptions if s["subscription_id"] == subscription_id), None)
    
    if not subscription:
        await callback.answer("Абонемент не найден", show_alert=True)
        return
    
    # Генерируем QR из сохранённого кода
    from utils.qr_generator import generate_qr_code
    qr_image = generate_qr_code(subscription["qr_code"])
    
    qr_bytes = qr_image.getvalue()
    await callback.message.answer_photo(
        photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
        caption="Твой QR-код для посещений"
    )
    await callback.answer()


@router.message(F.text == "📊 Статистика")
async def statistics(message: Message):
    """Показ статистики пользователя"""
    user_id = message.from_user.id
    stats = await db.get_visit_stats(user_id)
    
    visits = stats.get("visits_count", 0)
    total = stats.get("total_lessons", 0)
    remaining = stats.get("remaining_lessons", 0)
    missed = total - visits - remaining if total > 0 else 0
    regularity = int((visits / total * 100)) if total > 0 else 0
    
    text = "📊 Твоя активность:\n\n"
    text += f"Посещений: {visits} / {total}\n"
    text += f"Пропусков: {missed}\n"
    text += f"Средняя регулярность: {regularity}%"
    
    await message.answer(text)


@router.message(F.text == "🆘 Поддержка")
async def support(message: Message):
    """Поддержка"""
    await message.answer(
        "🆘 Поддержка\n\n"
        "Если у тебя есть вопросы, напиши нам:\n"
        "📧 support@example.com\n"
        "📱 +7 (XXX) XXX-XX-XX"
    )


@router.callback_query(F.data.startswith("cancel_payment_"))
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Отмена платежа"""
    try:
        subscription_id = int(callback.data.replace("cancel_payment_", ""))
        user_id = callback.from_user.id
        
        # Проверяем, что абонемент принадлежит пользователю
        subscription = await db.get_user_subscriptions(user_id)
        if not any(s.get("subscription_id") == subscription_id for s in subscription):
            # Проверяем через прямой запрос
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                async with db_conn.execute(
                    "SELECT * FROM subscriptions WHERE subscription_id = ? AND user_id = ?",
                    (subscription_id, user_id)
                ) as cursor:
                    sub = await cursor.fetchone()
                    if not sub:
                        await callback.answer("Абонемент не найден или доступ запрещен", show_alert=True)
                        return
        
        # Удаляем связанные платежи
        payments = await db.get_user_payments(user_id)
        for payment in payments:
            if payment.get("subscription_id") == subscription_id:
                # Помечаем платеж как отмененный
                await db.update_payment_status(
                    payment.get("payment_id"),
                    "cancelled",
                    error_message="Отменен пользователем"
                )
        
        # Удаляем временный абонемент
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as db_conn:
            await db_conn.execute("DELETE FROM subscriptions WHERE subscription_id = ?", (subscription_id,))
            await db_conn.commit()
        
        await callback.message.answer("❌ Платеж отменен. Абонемент не создан.")
        await callback.answer("Платеж отменен")
        await state.clear()
    except ValueError:
        await callback.answer("Ошибка: неверный ID абонемента", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отмене платежа: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при отмене платежа", show_alert=True)


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery, state: FSMContext):
    """Проверка статуса платежа"""
    payment_id = int(callback.data.replace("check_payment_", ""))
    user_id = callback.from_user.id
    
    try:
        from services.payment import AirbaPayClient, PaymentService
        from config import (
            AIRBA_PAY_BASE_URL, AIRBA_PAY_USER, AIRBA_PAY_PASSWORD,
            AIRBA_PAY_TERMINAL_ID, AIRBA_PAY_COMPANY_ID, AIRBA_PAY_WEBHOOK_URL
        )
        
        client = AirbaPayClient(
            base_url=AIRBA_PAY_BASE_URL,
            user=AIRBA_PAY_USER,
            password=AIRBA_PAY_PASSWORD,
            terminal_id=AIRBA_PAY_TERMINAL_ID,
            company_id=AIRBA_PAY_COMPANY_ID
        )
        
        payment_service = PaymentService(client, db, AIRBA_PAY_WEBHOOK_URL)
        result = await payment_service.get_payment_status(payment_id, user_id)
        
        if result.get("success"):
            status = result.get("status", "pending")
            payment = result.get("payment", {})
            subscription_id = payment.get("subscription_id")
            
            if status == "success":
                # Платеж успешен, активируем абонемент
                if subscription_id:
                    # Генерируем QR-код
                    qr_id, qr_image = generate_subscription_qr(user_id, subscription_id)
                    
                    # Обновляем QR-код в базе данных
                    import aiosqlite
                    async with aiosqlite.connect(db.db_path) as db_conn:
                        await db_conn.execute(
                            "UPDATE subscriptions SET qr_code = ? WHERE subscription_id = ?",
                            (qr_id, subscription_id)
                        )
                        await db_conn.commit()
                    
                    await callback.message.answer(
                        "✅ Платеж успешно выполнен!\n\n"
                        "🎉 Абонемент активирован!\n\n"
                        "Вот твой QR-код для посещений 👇"
                    )
                    
                    try:
                        qr_bytes = qr_image.getvalue()
                        await callback.message.answer_photo(
                            photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
                            caption="Твой QR-код для посещений"
                        )
                    except Exception:
                        await callback.message.answer(
                            f"QR-код создан!\nКод: {qr_id}\n\n"
                            f"Установите Pillow для отображения QR-кода как изображения."
                        )
                else:
                    await callback.message.answer("✅ Платеж успешно выполнен!")
                
                await state.clear()
            elif status == "failed":
                await callback.message.answer(
                    "❌ Платеж не прошел.\n\n"
                    "Попробуйте оплатить снова или обратитесь в поддержку."
                )
            else:
                await callback.message.answer(
                    f"⏳ Статус платежа: {status}\n\n"
                    "Ожидаем подтверждения платежа..."
                )
        else:
            await callback.message.answer(
                f"❌ Ошибка при проверке платежа:\n{result.get('error', 'Неизвестная ошибка')}"
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при проверке платежа: {e}", exc_info=True)
        await callback.message.answer(
            f"❌ Ошибка при проверке платежа.\n\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )
        await callback.answer()


@router.message(F.text == "💳 Мои платежи")
async def my_payments(message: Message):
    """Показ истории платежей пользователя"""
    user_id = message.from_user.id
    payments = await db.get_user_payments(user_id)
    
    if not payments:
        await message.answer("У тебя пока нет платежей.")
        return
    
    text = "💳 История платежей:\n\n"
    for payment in payments[:10]:  # Показываем последние 10
        status_emoji = {
            "success": "✅",
            "pending": "⏳",
            "failed": "❌",
            "refunded": "↩️"
        }.get(payment.get("status", "pending"), "❓")
        
        amount = payment.get("amount", 0)
        status = payment.get("status", "pending")
        created_at = payment.get("created_at", "")
        
        text += f"{status_emoji} {amount} ₸ - {status}\n"
        if created_at:
            text += f"   📅 {created_at[:10]}\n"
        text += "\n"
    
    await message.answer(text)

