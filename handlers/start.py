"""Хендлеры для команды /start и регистрации"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database
import keyboards.keyboards as kb
from keyboards.keyboards import format_group_text, format_groups_list, format_groups_list_multiline, get_schedule_message
from utils.matcher import check_and_notify_new_matches

router = Router()


class RegistrationStates(StatesGroup):
    """Состояния регистрации"""
    selecting_current_group = State()
    selecting_desired_groups = State()
    confirmation = State()


# Временное хранилище для данных регистрации
registration_data = {}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user_id = message.from_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    if await database.user_exists(user_id):
        # Показываем главное меню
        user = await database.get_user(user_id)
        desired = await database.get_desired_groups(user_id)
        desired_str = format_groups_list_multiline(desired)
        
        await message.answer(
            f"🏠 Главное меню\n\n"
            f"👤 Твоя группа: {format_group_text(user['current_group'])}\n\n"
            f"🎯 Ищешь:\n{desired_str}\n\n"
            f"Что хочешь сделать?",
            reply_markup=kb.get_main_menu_keyboard()
        )
    else:
        # Начинаем регистрацию
        # Сначала показываем расписание
        await message.answer(
            "👋 Привет! Я помогу тебе найти человека для обмена группами ИАД.\n\n"
            + get_schedule_message() + "\n"
            + "📍 Выбери свою группу:"
        )
        # Затем показываем кнопки выбора группы
        await message.answer(
            "Выбери группу, в которой ты сейчас учишься:",
            reply_markup=kb.get_group_selection_keyboard()
        )
        await state.set_state(RegistrationStates.selecting_current_group)


@router.callback_query(F.data.startswith("select_group_"), RegistrationStates.selecting_current_group)
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора текущей группы при регистрации"""
    group_num = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Сохраняем выбранную группу
    registration_data[user_id] = {
        'current_group': group_num,
        'desired_groups': set()
    }
    
    # Подтверждаем выбор группы
    await callback.message.edit_text(
        f"✅ Запомнил, твоя группа — ИАД-{group_num}"
    )
    
    # Показываем выбор желаемых групп (без расписания, оно уже было в первом сообщении)
    await callback.message.answer(
        "🎯 В какие группы хочешь перевестись?\n\n"
        "Выбери одну или несколько групп, потом нажми «Готово»",
        reply_markup=kb.get_desired_groups_keyboard(group_num, set())
    )
    
    await state.set_state(RegistrationStates.selecting_desired_groups)
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_desired_"))
async def process_desired_group_toggle(callback: CallbackQuery, state: FSMContext):
    """Обработка переключения желаемой группы"""
    group_num = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    if user_id not in registration_data:
        await callback.answer("❌ Ошибка. Начни заново с /start", show_alert=True)
        return
    
    # Переключаем состояние группы
    if group_num in registration_data[user_id]['desired_groups']:
        registration_data[user_id]['desired_groups'].remove(group_num)
    else:
        registration_data[user_id]['desired_groups'].add(group_num)
    
    current_group = registration_data[user_id]['current_group']
    selected = registration_data[user_id]['desired_groups']
    
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_desired_groups_keyboard(current_group, selected)
    )
    await callback.answer()


@router.callback_query(F.data == "desired_groups_done")
async def process_desired_groups_done(callback: CallbackQuery, state: FSMContext):
    """Обработка завершения выбора желаемых групп"""
    user_id = callback.from_user.id
    
    if user_id not in registration_data:
        await callback.answer("❌ Ошибка. Начни заново с /start", show_alert=True)
        return
    
    desired = registration_data[user_id]['desired_groups']
    
    if not desired:
        await callback.answer("❌ Выбери хотя бы одну группу!", show_alert=True)
        return
    
    current_group = registration_data[user_id]['current_group']
    desired_str = format_groups_list_multiline(sorted(desired))
    
    await callback.message.edit_text(
        f"📋 Проверь данные:\n\n"
        f"👤 Твоя группа: {format_group_text(current_group)}\n\n"
        f"🎯 Хочешь перевестись в:\n{desired_str}\n\n"
        f"Всё верно?",
        reply_markup=kb.get_confirmation_keyboard()
    )
    await state.set_state(RegistrationStates.confirmation)
    await callback.answer()


@router.callback_query(F.data == "confirm_registration")
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения регистрации"""
    user_id = callback.from_user.id
    
    if user_id not in registration_data:
        await callback.answer("❌ Ошибка. Начни заново с /start", show_alert=True)
        return
    
    data = registration_data[user_id]
    user = callback.from_user
    
    # Сохраняем в БД
    await database.create_user(
        telegram_id=user_id,
        username=user.username,
        first_name=user.first_name or "Пользователь",
        current_group=data['current_group']
    )
    
    await database.set_desired_groups(user_id, list(data['desired_groups']))
    
    # Очищаем временные данные
    del registration_data[user_id]
    await state.clear()
    
    # Проверяем мэтчи
    matches = await check_and_notify_new_matches(user_id, callback.bot)
    
    desired_str = format_groups_list_multiline(sorted(data['desired_groups']))
    
    text = (
        f"✅ Регистрация завершена!\n\n"
        f"👤 Твоя группа: {format_group_text(data['current_group'])}\n\n"
        f"🎯 Ищешь:\n{desired_str}\n\n"
    )
    
    if matches:
        text += f"🎉 Кстати, уже нашлось {len(matches)} мэтч(ей)! Проверь их в меню."
    else:
        text += "Как только появится мэтч — я сразу напишу!"
    
    await callback.message.edit_text(text)
    await callback.message.answer(
        "🏠 Главное меню\n\nЧто хочешь сделать?",
        reply_markup=kb.get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_registration")
async def process_edit_registration(callback: CallbackQuery, state: FSMContext):
    """Обработка редактирования данных регистрации"""
    await callback.message.edit_text(
        "📍 В какой группе ты сейчас учишься?",
        reply_markup=kb.get_group_selection_keyboard()
    )
    await state.set_state(RegistrationStates.selecting_current_group)
    await callback.answer()

