"""Клавиатуры для бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import GROUPS_COUNT, GROUP_SCHEDULE


def format_group_button(group_num: int, prefix: str = "") -> str:
    """Форматирование текста кнопки группы с расписанием"""
    schedule = GROUP_SCHEDULE[group_num]
    if prefix:
        return f"{prefix} ИАД-{group_num}\n⏰ {schedule}"
    return f"ИАД-{group_num}\n⏰ {schedule}"


def format_group_text(group_num: int) -> str:
    """Форматирование текста группы с расписанием для сообщений"""
    schedule = GROUP_SCHEDULE[group_num]
    return f"ИАД-{group_num} (⏰ {schedule})"


def format_groups_list(group_nums: list) -> str:
    """Форматирование списка групп с расписанием"""
    return ", ".join([format_group_text(g) for g in sorted(group_nums)])


def get_group_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора текущей группы (2 ряда по 5)"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, GROUPS_COUNT + 1):
        builder.button(text=format_group_button(i), callback_data=f"select_group_{i}")
    
    builder.adjust(5)  # 5 кнопок в ряду
    return builder.as_markup()


def get_desired_groups_keyboard(current_group: int, selected_groups: set = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора желаемых групп с toggle"""
    if selected_groups is None:
        selected_groups = set()
    
    builder = InlineKeyboardBuilder()
    
    for i in range(1, GROUPS_COUNT + 1):
        if i == current_group:
            continue  # Пропускаем текущую группу
        
        if i in selected_groups:
            builder.button(text=format_group_button(i, "✅"), callback_data=f"toggle_desired_{i}")
        else:
            builder.button(text=format_group_button(i, "⬜"), callback_data=f"toggle_desired_{i}")
    
    builder.adjust(5)  # 5 кнопок в ряду
    builder.button(text="✅ Готово", callback_data="desired_groups_done")
    
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения данных"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_registration")
    builder.button(text="✏️ Изменить", callback_data="edit_registration")
    return builder.as_markup()


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Проверить мэтчи")
    builder.button(text="✏️ Изменить мою группу")
    builder.button(text="🎯 Изменить желаемые")
    builder.button(text="🚪 Больше не ищу")
    builder.adjust(1)  # По одной кнопке в ряду
    return builder.as_markup(resize_keyboard=True)


def get_delete_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data="confirm_delete")
    builder.button(text="❌ Отмена", callback_data="cancel_delete")
    return builder.as_markup()

