import aiosqlite

DB_PATH = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                selection TEXT
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
