"""Тесты для keyboards/keyboards.py"""
import pytest
from keyboards import keyboards


def test_format_group_button():
    """Тест форматирования кнопки группы"""
    button_text = keyboards.format_group_button(1)
    assert "ИАД-1" in button_text
    assert "⏰" in button_text


def test_format_group_button_with_prefix():
    """Тест форматирования кнопки группы с префиксом"""
    button_text = keyboards.format_group_button(2, "✅")
    assert "✅" in button_text
    assert "ИАД-2" in button_text


def test_format_group_text():
    """Тест форматирования текста группы"""
    text = keyboards.format_group_text(3)
    assert "ИАД-3" in text
    assert "⏰" in text


def test_format_groups_list():
    """Тест форматирования списка групп через запятую"""
    groups = [1, 2, 3]
    result = keyboards.format_groups_list(groups)
    assert "ИАД-1" in result
    assert "ИАД-2" in result
    assert "ИАД-3" in result
    assert "," in result


def test_format_groups_list_multiline():
    """Тест форматирования списка групп многострочно"""
    groups = [1, 2, 3]
    result = keyboards.format_groups_list_multiline(groups)
    assert "ИАД-1" in result
    assert "ИАД-2" in result
    assert "ИАД-3" in result
    assert "\n" in result
    assert "•" in result


def test_get_schedule_message():
    """Тест получения сообщения с расписанием"""
    schedule = keyboards.get_schedule_message()
    assert "⏰ Расписание групп" in schedule
    assert "ИАД-1" in schedule
    assert "ИАД-10" in schedule


def test_get_group_selection_keyboard():
    """Тест клавиатуры выбора группы"""
    kb = keyboards.get_group_selection_keyboard()
    assert kb is not None
    # Проверяем, что есть кнопки для всех групп
    inline_keyboard = kb.inline_keyboard
    assert len(inline_keyboard) == 2  # 2 ряда по 5 кнопок
    assert len(inline_keyboard[0]) == 5
    assert len(inline_keyboard[1]) == 5


def test_get_desired_groups_keyboard():
    """Тест клавиатуры выбора желаемых групп"""
    kb = keyboards.get_desired_groups_keyboard(current_group=3, selected_groups={1, 2})
    assert kb is not None
    # Проверяем, что текущая группа не показывается
    inline_keyboard = kb.inline_keyboard
    all_buttons_text = " ".join([btn.text for row in inline_keyboard for btn in row])
    assert "ИАД-3" not in all_buttons_text


def test_get_desired_groups_keyboard_selected():
    """Тест клавиатуры с выбранными группами"""
    kb = keyboards.get_desired_groups_keyboard(current_group=1, selected_groups={2})
    inline_keyboard = kb.inline_keyboard
    all_buttons_text = " ".join([btn.text for row in inline_keyboard for btn in row])
    assert "✅ ИАД-2" in all_buttons_text or "✅" in all_buttons_text


def test_get_confirmation_keyboard():
    """Тест клавиатуры подтверждения"""
    kb = keyboards.get_confirmation_keyboard()
    assert kb is not None
    inline_keyboard = kb.inline_keyboard
    assert len(inline_keyboard) == 1
    assert len(inline_keyboard[0]) == 2  # Подтвердить и Изменить


def test_get_main_menu_keyboard():
    """Тест главного меню"""
    kb = keyboards.get_main_menu_keyboard()
    assert kb is not None
    keyboard = kb.keyboard
    assert len(keyboard) == 4  # 4 кнопки
    assert keyboard[0][0].text == "🔍 Проверить мэтчи"
    assert keyboard[1][0].text == "🚪 Больше не ищу"

