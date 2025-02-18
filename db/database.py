# db/database.py
import aiosqlite
import time

DB_PATH = "db/database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Создаем таблицы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                selection TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule_cache (
                name TEXT PRIMARY KEY,
                data TEXT,
                timestamp INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                name TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id TEXT PRIMARY KEY,
                name TEXT
            )
        """)
        await db.commit()

async def save_user_selection(user_id: int, selection: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (user_id, selection) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET selection = ?",
            (user_id, selection, selection)
        )
        await db.commit()

async def get_user_selection(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT selection FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()
            return [row[0] for row in users] if users else []

async def save_schedule_cache(name: str, data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO schedule_cache (name, data, timestamp) VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET data = ?, timestamp = ?",
            (name, data, int(time.time()), data, int(time.time()))
        )
        await db.commit()

async def get_schedule_cache(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT data, timestamp FROM schedule_cache WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
            if row and int(time.time()) - row[1] < 10800:  # 3 часа (10800 сек)
                return row[0]
            return None

async def save_groups_and_teachers(groups: list, teachers: list):
    async with aiosqlite.connect(DB_PATH) as db:
        # Очищаем таблицы перед добавлением новых данных
        await db.execute("DELETE FROM groups")
        await db.execute("DELETE FROM teachers")

        # Добавляем группы
        for group in groups:
            await db.execute("INSERT INTO groups (id, name) VALUES (?, ?)", (group["id"], group["name"]))

        # Добавляем преподавателей
        for teacher in teachers:
            await db.execute("INSERT INTO teachers (id, name) VALUES (?, ?)", (teacher["id"], teacher["name"]))

        await db.commit()

async def search_groups(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name FROM groups WHERE name LIKE ?", (f"%{query}%",)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def search_teachers(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name FROM teachers WHERE name LIKE ?", (f"%{query}%",)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]