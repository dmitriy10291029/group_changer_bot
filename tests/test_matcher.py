"""Тесты для utils/matcher.py"""
import pytest
import database
from utils import matcher


@pytest.mark.asyncio
async def test_find_matches_no_user(mock_config):
    """Тест поиска мэтчей для несуществующего пользователя"""
    await database.init_db()
    
    matches = await matcher.find_matches(99999)
    assert matches == []


@pytest.mark.asyncio
async def test_find_matches_no_desired_groups(mock_config):
    """Тест поиска мэтчей без желаемых групп"""
    await database.init_db()
    
    await database.create_user(111, "user1", "User 1", 1)
    
    matches = await matcher.find_matches(111)
    assert matches == []


@pytest.mark.asyncio
async def test_find_matches_simple_match(mock_config):
    """Тест поиска простого мэтча"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 1
    assert matches[0]['telegram_id'] == 222
    assert matches[0]['current_group'] == 2
    assert matches[0]['desired_group'] == 1


@pytest.mark.asyncio
async def test_find_matches_multiple_matches(mock_config):
    """Тест поиска нескольких мэтчей"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2 или 3
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2, 3])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # User 3: группа 3, хочет в группу 1
    await database.create_user(333, "user3", "User 3", 3)
    await database.set_desired_groups(333, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 2
    assert {m['telegram_id'] for m in matches} == {222, 333}


@pytest.mark.asyncio
async def test_find_matches_no_match(mock_config):
    """Тест поиска мэтчей когда их нет"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 3 (не в группу 1)
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [3])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_find_matches_exclude_self(mock_config):
    """Тест что мэтч не включает самого пользователя"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 1 (сам в себя)
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [1])
    
    matches = await matcher.find_matches(111)
    assert len(matches) == 0


@pytest.mark.asyncio
async def test_send_match_notification(mock_config):
    """Тест отправки уведомления о мэтче"""
    from unittest.mock import AsyncMock
    
    mock_bot = AsyncMock()
    match_user = {
        'username': 'testuser',
        'first_name': 'Test User',
        'current_group': 2,
        'desired_group': 1
    }
    
    result = await matcher.send_match_notification(mock_bot, 111, match_user)
    
    assert result is True
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_match_notification_no_username(mock_config):
    """Тест отправки уведомления без username"""
    from unittest.mock import AsyncMock
    
    mock_bot = AsyncMock()
    match_user = {
        'username': None,
        'first_name': 'Test User',
        'current_group': 2,
        'desired_group': 1
    }
    
    result = await matcher.send_match_notification(mock_bot, 111, match_user)
    
    assert result is True
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_find_matches_after_user_deleted(mock_config):
    """Тест поиска мэтчей после удаления пользователя (больше не ищу)"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # Проверяем, что мэтч есть
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 1
    assert matches_before[0]['telegram_id'] == 222
    
    # User 2 нажимает "Больше не ищу" - удаляется из базы
    await database.delete_user(222)
    
    # Проверяем, что мэтч исчез
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 0


@pytest.mark.asyncio
async def test_find_matches_deleted_user_not_in_results(mock_config):
    """Тест что удаленный пользователь не появляется в результатах поиска"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # User 3: группа 2, хочет в группу 1 (тоже мэтч для User 1)
    await database.create_user(333, "user3", "User 3", 2)
    await database.set_desired_groups(333, [1])
    
    # Проверяем, что есть 2 мэтча
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 2
    assert {m['telegram_id'] for m in matches_before} == {222, 333}
    
    # User 2 удаляется
    await database.delete_user(222)
    
    # Проверяем, что остался только User 3
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 1
    assert matches_after[0]['telegram_id'] == 333
    assert 222 not in {m['telegram_id'] for m in matches_after}


@pytest.mark.asyncio
async def test_find_matches_multiple_users_deleted(mock_config):
    """Тест поиска мэтчей после удаления нескольких пользователей"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2, 3, 4
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2, 3, 4])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # User 3: группа 3, хочет в группу 1
    await database.create_user(333, "user3", "User 3", 3)
    await database.set_desired_groups(333, [1])
    
    # User 4: группа 4, хочет в группу 1
    await database.create_user(444, "user4", "User 4", 4)
    await database.set_desired_groups(444, [1])
    
    # Проверяем, что есть 3 мэтча
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 3
    assert {m['telegram_id'] for m in matches_before} == {222, 333, 444}
    
    # Удаляем User 2 и User 4
    await database.delete_user(222)
    await database.delete_user(444)
    
    # Проверяем, что остался только User 3
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 1
    assert matches_after[0]['telegram_id'] == 333


@pytest.mark.asyncio
async def test_find_matches_bidirectional_after_deletion(mock_config):
    """Тест что мэтчи работают в обе стороны и корректно обновляются после удаления"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # Проверяем мэтчи в обе стороны
    matches_111 = await matcher.find_matches(111)
    matches_222 = await matcher.find_matches(222)
    
    assert len(matches_111) == 1
    assert matches_111[0]['telegram_id'] == 222
    assert len(matches_222) == 1
    assert matches_222[0]['telegram_id'] == 111
    
    # User 1 удаляется
    await database.delete_user(111)
    
    # Проверяем, что User 2 больше не видит мэтча
    matches_222_after = await matcher.find_matches(222)
    assert len(matches_222_after) == 0


@pytest.mark.asyncio
async def test_find_matches_partial_match_after_deletion(mock_config):
    """Тест частичного мэтча после удаления одного из участников"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2 и 3
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2, 3])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # User 3: группа 3, хочет в группу 1
    await database.create_user(333, "user3", "User 3", 3)
    await database.set_desired_groups(333, [1])
    
    # User 4: группа 4, хочет в группу 1 (но User 1 не хочет в группу 4)
    await database.create_user(444, "user4", "User 4", 4)
    await database.set_desired_groups(444, [1])
    
    # Проверяем мэтчи для User 1
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 2
    assert {m['telegram_id'] for m in matches_before} == {222, 333}
    
    # User 2 удаляется
    await database.delete_user(222)
    
    # Проверяем, что остался только User 3
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 1
    assert matches_after[0]['telegram_id'] == 333
    
    # User 4 все еще не мэтч для User 1 (User 1 не хочет в группу 4)
    assert 444 not in {m['telegram_id'] for m in matches_after}


@pytest.mark.asyncio
async def test_find_matches_no_matches_after_all_deleted(mock_config):
    """Тест что после удаления всех потенциальных мэтчей результат пустой"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # Проверяем мэтч
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 1
    
    # Удаляем единственного мэтча
    await database.delete_user(222)
    
    # Проверяем, что мэтчей нет
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 0


@pytest.mark.asyncio
async def test_find_matches_cascade_deletion(mock_config):
    """Тест что CASCADE удаление желаемых групп не влияет на поиск мэтчей"""
    await database.init_db()
    
    # User 1: группа 1, хочет в группу 2
    await database.create_user(111, "user1", "User 1", 1)
    await database.set_desired_groups(111, [2])
    
    # User 2: группа 2, хочет в группу 1
    await database.create_user(222, "user2", "User 2", 2)
    await database.set_desired_groups(222, [1])
    
    # Проверяем мэтч
    matches_before = await matcher.find_matches(111)
    assert len(matches_before) == 1
    
    # Удаляем User 2 (CASCADE удалит его желаемые группы)
    await database.delete_user(222)
    
    # Проверяем, что мэтч исчез
    matches_after = await matcher.find_matches(111)
    assert len(matches_after) == 0
    
    # Проверяем, что желаемые группы User 2 действительно удалены
    desired_222 = await database.get_desired_groups(222)
    assert len(desired_222) == 0

