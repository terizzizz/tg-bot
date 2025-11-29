from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from utils.keyboards import get_main_menu, get_parent_menu, get_child_menu, get_parent_start_keyboard
from config import ROLE_USER, ROLE_PARENT, ROLE_CHILD

router = Router()
db = Database()


class StartStates(StatesGroup):
    waiting_for_child_name = State()
    waiting_for_child_age = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Операция отменена.\n\n"
            "Выберите действие из меню.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer("Нет активной операции для отмены.")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Обработка /start от пользователя {message.from_user.id}")
        
        user_id = message.from_user.id
        username = message.from_user.username
        full_name = message.from_user.full_name or message.from_user.first_name
        
        # Создаём или получаем пользователя
        user = await db.get_user(user_id)
        if not user:
            await db.create_user(user_id, username, full_name)
            user = await db.get_user(user_id)
            logger.info(f"Создан новый пользователь: {user_id}")
        
        role = user.get("role", ROLE_USER)
        logger.info(f"Роль пользователя {user_id}: {role}")
        
        if role == ROLE_PARENT:
            # Проверяем, есть ли уже дети
            children = await db.get_children(user_id)
            if not children:
                await message.answer(
                    "👋 Привет!\n\n"
                    "Ты родитель? Хотите добавить ребёнка?",
                    reply_markup=get_parent_start_keyboard()
                )
            else:
                await message.answer(
                    "👋 Добро пожаловать!\n\n"
                    "Выбери действие:",
                    reply_markup=get_parent_menu()
                )
        elif role == ROLE_CHILD:
            await message.answer(
                "👋 Привет!\n\n"
                "Я буду показывать твой QR-код и расписание.",
                reply_markup=get_child_menu()
            )
        else:
            await message.answer(
                "👋 Привет!\n\n"
                "Здесь ты можешь находить образовательные центры, покупать абонементы "
                "и посещать занятия по QR-коду.\n\n"
                "Выбери действие:",
                reply_markup=get_main_menu()
            )
        
        logger.info(f"Успешно обработан /start для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при обработке команды.\n\n"
            "Попробуйте ещё раз или обратитесь в поддержку."
        )

