import asyncpg

DB_CONFIG = {
    "user": "postgres",
    "password": "YtMine-Yyura",
    "database": "postgres",   # ✅ ИСПРАВИЛИ
    "host": "127.0.0.1",
    "port": 5432
}

pool = None


async def create_pool():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)


async def execute(query, *args):
    async with pool.acquire() as conn:
        await conn.execute(query, *args)

async def fetch(query, *args):
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def fetchrow(query, *args):
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def create_tables():
    # users
    await execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        username TEXT
    );
    """)

    # club_members
    await execute("""
    CREATE TABLE IF NOT EXISTS club_members (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        club_id INTEGER
    );
    """)

    # invites
    await execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id SERIAL PRIMARY KEY,
        code TEXT UNIQUE,
        type TEXT,
        target_id BIGINT,
        created_by BIGINT,
        uses INTEGER DEFAULT 0,
        max_uses INTEGER DEFAULT 1,
        expires_at TIMESTAMP
    );
    """)

    # events
    await execute("""
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        creator_id BIGINT,
        game TEXT,
        event_date TEXT,
        max_players INTEGER,
        description TEXT
    );
    """)

    # 🔥 RSVP таблица (обязательно добавь)
    await execute("""
    CREATE TABLE IF NOT EXISTS event_participants (
        id SERIAL PRIMARY KEY,
        event_id INTEGER,
        user_id BIGINT,
        status TEXT,
        UNIQUE(event_id, user_id)
    );
    """)

    await execute("""
    CREATE TABLE IF NOT EXISTS clubs (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        owner_id BIGINT
    )
    """)