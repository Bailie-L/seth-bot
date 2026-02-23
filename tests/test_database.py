"""Tests for database.py — uses temporary in-memory DB"""
import pytest
import aiosqlite

# Patch DATABASE_PATH before importing database module
import database
database.DATABASE_PATH = ":memory:"


@pytest.fixture
async def db():
    """Create a fresh in-memory database for each test"""
    conn = await aiosqlite.connect(":memory:")

    # Create core tables
    await conn.execute('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            discord_name TEXT NOT NULL,
            is_premium INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE seths (
            seth_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            generation INTEGER DEFAULT 1,
            health INTEGER DEFAULT 100,
            hunger INTEGER DEFAULT 0,
            is_alive INTEGER DEFAULT 1,
            birth_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            death_time TIMESTAMP,
            death_reason TEXT,
            parent_id INTEGER
        )
    ''')
    await conn.execute('''
        CREATE TABLE resources (
            user_id INTEGER PRIMARY KEY,
            food INTEGER DEFAULT 5,
            medicine INTEGER DEFAULT 2,
            coal INTEGER DEFAULT 0,
            last_mine_time TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE graveyard (
            seth_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            generation INTEGER,
            lived_days INTEGER,
            death_reason TEXT,
            death_time TIMESTAMP,
            memorial_message TEXT
        )
    ''')
    await conn.commit()
    yield conn
    await conn.close()


class TestUserCreation:
    @pytest.mark.asyncio
    async def test_insert_user(self, db):
        await db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (12345, "TestUser#1234")
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM users WHERE user_id = 12345")
        user = await cursor.fetchone()
        assert user is not None
        assert user[1] == "TestUser#1234"

    @pytest.mark.asyncio
    async def test_duplicate_user_rejected(self, db):
        await db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (12345, "TestUser")
        )
        await db.commit()
        with pytest.raises(Exception):
            await db.execute(
                "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
                (12345, "Duplicate")
            )

    @pytest.mark.asyncio
    async def test_premium_defaults_to_zero(self, db):
        await db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (99999, "FreeUser")
        )
        await db.commit()
        cursor = await db.execute("SELECT is_premium FROM users WHERE user_id = 99999")
        row = await cursor.fetchone()
        assert row[0] == 0


class TestSethLifecycle:
    @pytest.mark.asyncio
    async def test_create_seth(self, db):
        await db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (1, "Owner")
        )
        await db.execute(
            "INSERT INTO seths (user_id, name, generation) VALUES (?, ?, ?)",
            (1, "Baby Seth", 1)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM seths WHERE user_id = 1")
        seth = await cursor.fetchone()
        assert seth is not None
        assert seth[2] == "Baby Seth"  # name
        assert seth[4] == 100  # health
        assert seth[5] == 0   # hunger
        assert seth[6] == 1   # is_alive

    @pytest.mark.asyncio
    async def test_kill_seth(self, db):
        await db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (1, "Owner")
        )
        await db.execute(
            "INSERT INTO seths (user_id, name) VALUES (?, ?)",
            (1, "Doomed Seth")
        )
        await db.commit()

        await db.execute(
            "UPDATE seths SET is_alive = 0, death_reason = ? WHERE user_id = ? AND is_alive = 1",
            ("Starvation", 1)
        )
        await db.commit()

        cursor = await db.execute("SELECT is_alive, death_reason FROM seths WHERE user_id = 1")
        seth = await cursor.fetchone()
        assert seth[0] == 0
        assert seth[1] == "Starvation"

    @pytest.mark.asyncio
    async def test_generation_tracking(self, db):
        await db.execute("INSERT INTO users (user_id, discord_name) VALUES (1, 'Owner')")
        await db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen1', 1, 0)")
        await db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen2', 2, 0)")
        await db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen3', 3, 1)")
        await db.commit()

        cursor = await db.execute("SELECT MAX(generation) FROM seths WHERE user_id = 1")
        result = await cursor.fetchone()
        assert result[0] == 3

    @pytest.mark.asyncio
    async def test_only_one_alive_query(self, db):
        await db.execute("INSERT INTO users (user_id, discord_name) VALUES (1, 'Owner')")
        await db.execute("INSERT INTO seths (user_id, name, is_alive) VALUES (1, 'Dead', 0)")
        await db.execute("INSERT INTO seths (user_id, name, is_alive) VALUES (1, 'Alive', 1)")
        await db.commit()

        cursor = await db.execute("SELECT name FROM seths WHERE user_id = 1 AND is_alive = 1")
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "Alive"


class TestResources:
    @pytest.mark.asyncio
    async def test_default_resources(self, db):
        await db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        await db.commit()
        cursor = await db.execute("SELECT food, medicine, coal FROM resources WHERE user_id = 1")
        row = await cursor.fetchone()
        assert row == (5, 2, 0)

    @pytest.mark.asyncio
    async def test_update_resources_after_mining(self, db):
        await db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        await db.commit()
        await db.execute("UPDATE resources SET food = food + 3 WHERE user_id = 1")
        await db.commit()
        cursor = await db.execute("SELECT food FROM resources WHERE user_id = 1")
        row = await cursor.fetchone()
        assert row[0] == 8

    @pytest.mark.asyncio
    async def test_feeding_reduces_food(self, db):
        await db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        await db.commit()
        await db.execute("UPDATE resources SET food = food - 1 WHERE user_id = 1 AND food > 0")
        await db.commit()
        cursor = await db.execute("SELECT food FROM resources WHERE user_id = 1")
        row = await cursor.fetchone()
        assert row[0] == 4


class TestGraveyard:
    @pytest.mark.asyncio
    async def test_add_to_graveyard(self, db):
        await db.execute(
            "INSERT INTO graveyard (seth_id, user_id, name, generation, lived_days, death_reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (1, 100, "Fallen Seth", 3, 7, "Starvation")
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM graveyard WHERE seth_id = 1")
        grave = await cursor.fetchone()
        assert grave[2] == "Fallen Seth"
        assert grave[3] == 3
        assert grave[5] == "Starvation"


