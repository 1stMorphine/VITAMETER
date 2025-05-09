import aiosqlite
from datetime import datetime

DB_PATH = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                birth_date TEXT,
                reminder_day INTEGER,
                reminder_hour INTEGER,
                reminder_minute INTEGER
            )
        ''')
        await db.commit()

async def set_birth_date(user_id: int, birth_date: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users(user_id, birth_date) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET birth_date = excluded.birth_date
        ''', (user_id, birth_date.isoformat()))
        await db.commit()

async def get_birth_date(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT birth_date FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return datetime.fromisoformat(row[0]) if row and row[0] else None

async def delete_birth_date(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE users SET birth_date = NULL WHERE user_id = ?', (user_id,))
        await db.commit()

async def set_reminder(user_id: int, day: int, hour: int, minute: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users(user_id, reminder_day, reminder_hour, reminder_minute)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET reminder_day=?, reminder_hour=?, reminder_minute=?
        ''', (user_id, day, hour, minute, day, hour, minute))
        await db.commit()

async def get_reminder(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''SELECT reminder_day, reminder_hour, reminder_minute FROM users WHERE user_id = ?''', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row if row else None
