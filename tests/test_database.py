"""Тесты для database.py"""
import pytest
import aiosqlite
import database
from datetime import datetime


@pytest.mark.asyncio
async def test_init_db(mock_config):
    """Тест инициализации базы данных"""
    await database.init_db()
    
    # Проверяем, что таблицы созданы
    async with aiosqlite.connect(mock_config) as db:
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cursor:
            tables = [row[0] for row in await cursor.fetchall()]
            assert 'users' in tables
            assert 'desired_groups' in tables


@pytest.mark.asyncio
async def test_create_user(mock_config):
    """Тест создания пользователя"""
    await database.init_db()
    
    await database.create_user(
        telegram_id=12345,
        username="testuser",
        first_name="Test User",
        current_group=3
    )
    
    user = await database.get_user(12345)
    assert user is not None
    assert user['telegram_id'] == 12345
    assert user['username'] == "testuser"
    assert user['first_name'] == "Test User"
    assert user['current_group'] == 3


@pytest.mark.asyncio
async def test_user_exists(mock_config):
    """Тест проверки существования пользователя"""
    await database.init_db()
    
    assert await database.user_exists(12345) is False
    
    await database.create_user(12345, "test", "Test", 1)
    
    assert await database.user_exists(12345) is True


@pytest.mark.asyncio
async def test_set_desired_groups(mock_config):
    """Тест установки желаемых групп"""
    await database.init_db()
    
    await database.create_user(12345, "test", "Test", 1)
    await database.set_desired_groups(12345, [2, 3, 4])
    
    desired = await database.get_desired_groups(12345)
    assert set(desired) == {2, 3, 4}


@pytest.mark.asyncio
async def test_update_desired_groups(mock_config):
    """Тест обновления желаемых групп"""
    await database.init_db()
    
    await database.create_user(12345, "test", "Test", 1)
    await database.set_desired_groups(12345, [2, 3])
    
    # Обновляем на другие группы
    await database.set_desired_groups(12345, [4, 5])
    
    desired = await database.get_desired_groups(12345)
    assert set(desired) == {4, 5}


@pytest.mark.asyncio
async def test_update_user_group(mock_config):
    """Тест обновления текущей группы пользователя"""
    await database.init_db()
    
    await database.create_user(12345, "test", "Test", 1)
    await database.update_user_group(12345, 5)
    
    user = await database.get_user(12345)
    assert user['current_group'] == 5


@pytest.mark.asyncio
async def test_get_users_from_group(mock_config):
    """Тест получения пользователей из группы"""
    await database.init_db()
    
    await database.create_user(111, "user1", "User 1", 1)
    await database.create_user(222, "user2", "User 2", 1)
    await database.create_user(333, "user3", "User 3", 2)
    
    users_group_1 = await database.get_users_from_group(1)
    assert len(users_group_1) == 2
    assert {u['telegram_id'] for u in users_group_1} == {111, 222}
    
    users_group_2 = await database.get_users_from_group(2)
    assert len(users_group_2) == 1
    assert users_group_2[0]['telegram_id'] == 333


@pytest.mark.asyncio
async def test_delete_user(mock_config):
    """Тест удаления пользователя"""
    await database.init_db()
    
    await database.create_user(12345, "test", "Test", 1)
    await database.set_desired_groups(12345, [2, 3])
    
    assert await database.user_exists(12345) is True
    
    await database.delete_user(12345)
    
    assert await database.user_exists(12345) is False
    
    # Проверяем, что желаемые группы тоже удалены (CASCADE)
    desired = await database.get_desired_groups(12345)
    assert len(desired) == 0

