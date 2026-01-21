"""Хендлеры для редактирования профиля"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database
import keyboards.keyboards as kb
from keyboards.keyboards import format_group_text, format_groups_list_multiline, get_schedule_message
from utils.matcher import check_and_notify_new_matches

router = Router()


class EditStates(StatesGroup):
    """Состояния редактирования"""
    editing_current_group = State()
    editing_desired_groups = State()
    confirming_current_group = State()
    confirming_desired_groups = State()


# Временное хранилище для данных редактирования
edit_data = {}


@router.message(F.text == "✏️ Изменить мою группу")
async def start_edit_current_group(message: Message, state: FSMContext):
    """Начало редактирования текущей группы"""
    user_id = message.from_user.id
    
    if not await database.user_exists(user_id):
        await message.answer("❌ Ты ещё не зарегистрирован. Используй /start")
        return
    
    await message.answer(
        "📍 В какой группе ты сейчас учишься?",
        reply_markup=kb.get_group_selection_keyboard()
    )
    await state.set_state(EditStates.editing_current_group)


@router.message(F.text == "🎯 Изменить желаемые")
async def start_edit_desired_groups(message: Message, state: FSMContext):
    """Начало редактирования желаемых групп"""
    user_id = message.from_user.id
    
    if not await database.user_exists(user_id):
        await message.answer("❌ Ты ещё не зарегистрирован. Используй /start")
        return
    
    user = await database.get_user(user_id)
    current_desired = set(await database.get_desired_groups(user_id))
    
    edit_data[user_id] = {
        'desired_groups': current_desired.copy()
    }
    
    await message.answer(
        "🎯 В какие группы хочешь перевестись?\n\n"
        "Выбери одну или несколько групп, потом нажми «Готово»",
        reply_markup=kb.get_desired_groups_keyboard(user['current_group'], current_desired)
    )
    await state.set_state(EditStates.editing_desired_groups)


@router.callback_query(F.data.startswith("select_group_"), EditStates.editing_current_group)
async def process_edit_current_group(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора новой текущей группы"""
    group_num = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Сохраняем выбранную группу для подтверждения
    edit_data[user_id] = {
        'current_group': group_num
    }
    
    user = await database.get_user(user_id)
    desired = await database.get_desired_groups(user_id)
    desired_str = format_groups_list_multiline(desired)
    
    # Показываем подтверждение
    await callback.message.edit_text(
        f"📋 Проверь данные:\n\n"
        f"👤 Твоя группа: {format_group_text(group_num)}\n\n"
        f"🎯 Хочешь перевестись в:\n{desired_str}\n\n"
        f"Всё верно?",
        reply_markup=kb.get_confirmation_keyboard("confirm_edit_current_group", "edit_current_group_again")
    )
    await state.set_state(EditStates.confirming_current_group)
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_desired_"), EditStates.editing_desired_groups)
async def process_edit_desired_toggle(callback: CallbackQuery, state: FSMContext):
    """Обработка переключения желаемой группы при редактировании"""
    group_num = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    if user_id not in edit_data:
        await callback.answer("❌ Ошибка. Начни заново", show_alert=True)
        return
    
    # Переключаем состояние группы
    if group_num in edit_data[user_id]['desired_groups']:
        edit_data[user_id]['desired_groups'].remove(group_num)
    else:
        edit_data[user_id]['desired_groups'].add(group_num)
    
    user = await database.get_user(user_id)
    selected = edit_data[user_id]['desired_groups']
    
    await callback.message.edit_reply_markup(
        reply_markup=kb.get_desired_groups_keyboard(user['current_group'], selected)
    )
    await callback.answer()


@router.callback_query(F.data == "desired_groups_done", EditStates.editing_desired_groups)
async def process_edit_desired_done(callback: CallbackQuery, state: FSMContext):
    """Обработка завершения редактирования желаемых групп"""
    user_id = callback.from_user.id
    
    if user_id not in edit_data:
        await callback.answer("❌ Ошибка. Начни заново", show_alert=True)
        return
    
    desired = edit_data[user_id]['desired_groups']
    
    if not desired:
        await callback.answer("❌ Выбери хотя бы одну группу!", show_alert=True)
        return
    
    user = await database.get_user(user_id)
    desired_str = format_groups_list_multiline(sorted(desired))
    
    # Показываем подтверждение
    await callback.message.edit_text(
        f"📋 Проверь данные:\n\n"
        f"👤 Твоя группа: {format_group_text(user['current_group'])}\n\n"
        f"🎯 Хочешь перевестись в:\n{desired_str}\n\n"
        f"Всё верно?",
        reply_markup=kb.get_confirmation_keyboard("confirm_edit_desired_groups", "edit_desired_groups_again")
    )
    await state.set_state(EditStates.confirming_desired_groups)
    await callback.answer()


@router.message(F.text == "🚪 Больше не ищу")
async def start_delete_user(message: Message):
    """Начало процесса удаления пользователя"""
    user_id = message.from_user.id
    
    if not await database.user_exists(user_id):
        await message.answer("❌ Ты ещё не зарегистрирован. Используй /start")
        return
    
    await message.answer(
        "🚪 Ты уверен, что хочешь удалить свои данные?\n\n"
        "Тебя больше не будут находить для обмена, и ты не будешь получать уведомления.",
        reply_markup=kb.get_delete_confirmation_keyboard()
    )


@router.callback_query(F.data == "confirm_delete")
async def process_delete_user(callback: CallbackQuery):
    """Подтверждение удаления пользователя"""
    user_id = callback.from_user.id
    
    await database.delete_user(user_id)
    
    await callback.message.edit_text(
        "👋 Данные удалены!\n\n"
        "Если передумаешь — просто напиши /start"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def process_cancel_delete(callback: CallbackQuery):
    """Отмена удаления"""
    await callback.message.delete()
    await callback.answer("❌ Удаление отменено")


@router.callback_query(F.data == "confirm_edit_current_group")
async def process_confirm_edit_current_group(callback: CallbackQuery, state: FSMContext):
    """Подтверждение изменения текущей группы"""
    user_id = callback.from_user.id
    
    if user_id not in edit_data or 'current_group' not in edit_data[user_id]:
        await callback.answer("❌ Ошибка. Начни заново", show_alert=True)
        return
    
    group_num = edit_data[user_id]['current_group']
    
    # Получаем текущие желаемые группы
    current_desired = set(await database.get_desired_groups(user_id))
    
    # Проверяем, не совпадает ли новая группа с одной из желаемых
    if group_num in current_desired:
        if len(current_desired) > 1:
            # Если желаемых групп больше 1 - автоматически исключаем новую текущую группу
            current_desired.remove(group_num)
            await database.set_desired_groups(user_id, list(current_desired))
            
            # Обновляем группу в БД
            await database.update_user_group(user_id, group_num)
            
            # Проверяем мэтчи
            matches = await check_and_notify_new_matches(user_id, callback.bot)
            
            desired_str = format_groups_list_multiline(sorted(current_desired))
            
            text = (
                f"✅ Группа обновлена!\n\n"
                f"👤 Твоя группа: {format_group_text(group_num)}\n\n"
                f"ℹ️ Ты указал свою группу как одну из желаемых, поэтому я убрал её из списка желаемых групп.\n\n"
                f"🎯 Ищешь:\n{desired_str}\n\n"
            )
            
            if matches:
                text += f"🎉 Нашлось {len(matches)} новых мэтч(ей)! Проверь их в меню."
            
            await callback.message.edit_text(text)
            await callback.message.answer(
                "🏠 Главное меню",
                reply_markup=kb.get_main_menu_keyboard()
            )
        else:
            # Если желаемая группа была только одна - просим выбрать новую
            await callback.message.edit_text(
                f"⚠️ Ты указал свою группу как ту, в которую хотел перевестись.\n\n"
                f"Так как ты теперь в группе {format_group_text(group_num)}, нужно выбрать новую группу, куда ты хочешь перевестись.\n\n"
                f"Нажми «🎯 Изменить желаемые» в главном меню, чтобы выбрать новую группу."
            )
            await callback.message.answer(
                "🏠 Главное меню",
                reply_markup=kb.get_main_menu_keyboard()
            )
            # Удаляем желаемую группу, так как она совпадает с текущей
            await database.set_desired_groups(user_id, [])
    else:
        # Обычное обновление группы
        await database.update_user_group(user_id, group_num)
        
        # Проверяем мэтчи
        matches = await check_and_notify_new_matches(user_id, callback.bot)
        
        user = await database.get_user(user_id)
        desired = await database.get_desired_groups(user_id)
        desired_str = format_groups_list_multiline(desired)
        
        text = (
            f"✅ Группа обновлена!\n\n"
            f"👤 Твоя группа: {format_group_text(group_num)}\n\n"
            f"🎯 Ищешь:\n{desired_str}\n\n"
        )
        
        if matches:
            text += f"🎉 Нашлось {len(matches)} новых мэтч(ей)! Проверь их в меню."
        
        await callback.message.edit_text(text)
        await callback.message.answer(
            "🏠 Главное меню",
            reply_markup=kb.get_main_menu_keyboard()
        )
    
    del edit_data[user_id]
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_current_group_again")
async def process_edit_current_group_again(callback: CallbackQuery, state: FSMContext):
    """Возврат к редактированию текущей группы"""
    await callback.message.edit_text(
        "📍 В какой группе ты сейчас учишься?",
        reply_markup=kb.get_group_selection_keyboard()
    )
    await state.set_state(EditStates.editing_current_group)
    await callback.answer()


@router.callback_query(F.data == "confirm_edit_desired_groups")
async def process_confirm_edit_desired_groups(callback: CallbackQuery, state: FSMContext):
    """Подтверждение изменения желаемых групп"""
    user_id = callback.from_user.id
    
    if user_id not in edit_data or 'desired_groups' not in edit_data[user_id]:
        await callback.answer("❌ Ошибка. Начни заново", show_alert=True)
        return
    
    desired = edit_data[user_id]['desired_groups']
    
    # Обновляем в БД
    await database.set_desired_groups(user_id, list(desired))
    
    # Проверяем мэтчи
    matches = await check_and_notify_new_matches(user_id, callback.bot)
    
    desired_str = format_groups_list_multiline(sorted(desired))
    user = await database.get_user(user_id)
    
    text = (
        f"✅ Желаемые группы обновлены!\n\n"
        f"👤 Твоя группа: {format_group_text(user['current_group'])}\n\n"
        f"🎯 Ищешь:\n{desired_str}\n\n"
    )
    
    if matches:
        text += f"🎉 Нашлось {len(matches)} новых мэтч(ей)! Проверь их в меню."
    
    await callback.message.edit_text(text)
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=kb.get_main_menu_keyboard()
    )
    
    del edit_data[user_id]
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_desired_groups_again")
async def process_edit_desired_groups_again(callback: CallbackQuery, state: FSMContext):
    """Возврат к редактированию желаемых групп"""
    user_id = callback.from_user.id
    
    if user_id not in edit_data:
        await callback.answer("❌ Ошибка. Начни заново", show_alert=True)
        return
    
    user = await database.get_user(user_id)
    selected = edit_data[user_id]['desired_groups']
    
    await callback.message.edit_text(
        "🎯 В какие группы хочешь перевестись?\n\n"
        "Выбери одну или несколько групп, потом нажми «Готово»",
        reply_markup=kb.get_desired_groups_keyboard(user['current_group'], selected)
    )
    await state.set_state(EditStates.editing_desired_groups)
    await callback.answer()

