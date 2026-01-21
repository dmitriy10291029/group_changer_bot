"""Работа с базой данных"""
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict
from config import DATABASE_PATH


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                current_group INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Таблица желаемых групп
        await db.execute("""
            CREATE TABLE IF NOT EXISTS desired_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                desired_group INTEGER,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        """)
        
        await db.commit()


async def user_exists(telegram_id: int) -> bool:
    """Проверка существования пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def create_user(telegram_id: int, username: Optional[str], first_name: str, current_group: int):
    """Создание нового пользователя"""
    now = datetime.now()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name, current_group, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, username, first_name, current_group, now, now))
        await db.commit()


async def update_user_group(telegram_id: int, current_group: int):
    """Обновление текущей группы пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET current_group = ?, updated_at = ?
            WHERE telegram_id = ?
        """, (current_group, datetime.now(), telegram_id))
        await db.commit()


async def set_desired_groups(telegram_id: int, desired_groups: List[int]):
    """Установка желаемых групп (удаляет старые и добавляет новые)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Удаляем старые желаемые группы
        await db.execute("DELETE FROM desired_groups WHERE telegram_id = ?", (telegram_id,))
        
        # Добавляем новые
        for group in desired_groups:
            await db.execute(
                "INSERT INTO desired_groups (telegram_id, desired_group) VALUES (?, ?)",
                (telegram_id, group)
            )
        
        await db.commit()


async def get_user(telegram_id: int) -> Optional[Dict]:
    """Получение данных пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def get_desired_groups(telegram_id: int) -> List[int]:
    """Получение списка желаемых групп пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT desired_group FROM desired_groups WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_users_from_group(group: int) -> List[Dict]:
    """Получение всех пользователей из указанной группы"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE current_group = ?", (group,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def delete_user(telegram_id: int):
    """Удаление пользователя из базы (CASCADE удалит и желаемые группы)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def get_all_users() -> List[Dict]:
    """Получение всех пользователей (для отладки)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

