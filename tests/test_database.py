"""Tests for database schema — uses stdlib sqlite3 with in-memory DB"""
import sqlite3
import pytest


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test"""
    conn = sqlite3.connect(":memory:")

    # Create core tables
    conn.execute('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            discord_name TEXT NOT NULL,
            is_premium INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
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
    conn.execute('''
        CREATE TABLE resources (
            user_id INTEGER PRIMARY KEY,
            food INTEGER DEFAULT 5,
            medicine INTEGER DEFAULT 2,
            coal INTEGER DEFAULT 0,
            last_mine_time TIMESTAMP
        )
    ''')
    conn.execute('''
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
    conn.commit()
    yield conn
    conn.close()


class TestUserCreation:
    def test_insert_user(self, db):
        db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (12345, "TestUser#1234")
        )
        db.commit()
        cursor = db.execute("SELECT * FROM users WHERE user_id = 12345")
        user = cursor.fetchone()
        assert user is not None
        assert user[1] == "TestUser#1234"

    def test_duplicate_user_rejected(self, db):
        db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (12345, "TestUser")
        )
        db.commit()
        with pytest.raises(Exception):
            db.execute(
                "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
                (12345, "Duplicate")
            )

    def test_premium_defaults_to_zero(self, db):
        db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (99999, "FreeUser")
        )
        db.commit()
        cursor = db.execute("SELECT is_premium FROM users WHERE user_id = 99999")
        row = cursor.fetchone()
        assert row[0] == 0


class TestSethLifecycle:
    def test_create_seth(self, db):
        db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (1, "Owner")
        )
        db.execute(
            "INSERT INTO seths (user_id, name, generation) VALUES (?, ?, ?)",
            (1, "Baby Seth", 1)
        )
        db.commit()
        cursor = db.execute("SELECT * FROM seths WHERE user_id = 1")
        seth = cursor.fetchone()
        assert seth is not None
        assert seth[2] == "Baby Seth"  # name
        assert seth[4] == 100  # health
        assert seth[5] == 0   # hunger
        assert seth[6] == 1   # is_alive

    def test_kill_seth(self, db):
        db.execute(
            "INSERT INTO users (user_id, discord_name) VALUES (?, ?)",
            (1, "Owner")
        )
        db.execute(
            "INSERT INTO seths (user_id, name) VALUES (?, ?)",
            (1, "Doomed Seth")
        )
        db.commit()

        db.execute(
            "UPDATE seths SET is_alive = 0, death_reason = ? WHERE user_id = ? AND is_alive = 1",
            ("Starvation", 1)
        )
        db.commit()

        cursor = db.execute("SELECT is_alive, death_reason FROM seths WHERE user_id = 1")
        seth = cursor.fetchone()
        assert seth[0] == 0
        assert seth[1] == "Starvation"

    def test_generation_tracking(self, db):
        db.execute("INSERT INTO users (user_id, discord_name) VALUES (1, 'Owner')")
        db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen1', 1, 0)")
        db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen2', 2, 0)")
        db.execute("INSERT INTO seths (user_id, name, generation, is_alive) VALUES (1, 'Gen3', 3, 1)")
        db.commit()

        cursor = db.execute("SELECT MAX(generation) FROM seths WHERE user_id = 1")
        result = cursor.fetchone()
        assert result[0] == 3

    def test_only_one_alive_query(self, db):
        db.execute("INSERT INTO users (user_id, discord_name) VALUES (1, 'Owner')")
        db.execute("INSERT INTO seths (user_id, name, is_alive) VALUES (1, 'Dead', 0)")
        db.execute("INSERT INTO seths (user_id, name, is_alive) VALUES (1, 'Alive', 1)")
        db.commit()

        cursor = db.execute("SELECT name FROM seths WHERE user_id = 1 AND is_alive = 1")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "Alive"


class TestResources:
    def test_default_resources(self, db):
        db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        db.commit()
        cursor = db.execute("SELECT food, medicine, coal FROM resources WHERE user_id = 1")
        row = cursor.fetchone()
        assert row == (5, 2, 0)

    def test_update_resources_after_mining(self, db):
        db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        db.commit()
        db.execute("UPDATE resources SET food = food + 3 WHERE user_id = 1")
        db.commit()
        cursor = db.execute("SELECT food FROM resources WHERE user_id = 1")
        row = cursor.fetchone()
        assert row[0] == 8

    def test_feeding_reduces_food(self, db):
        db.execute("INSERT INTO resources (user_id) VALUES (?)", (1,))
        db.commit()
        db.execute("UPDATE resources SET food = food - 1 WHERE user_id = 1 AND food > 0")
        db.commit()
        cursor = db.execute("SELECT food FROM resources WHERE user_id = 1")
        row = cursor.fetchone()
        assert row[0] == 4


class TestGraveyard:
    def test_add_to_graveyard(self, db):
        db.execute(
            "INSERT INTO graveyard (seth_id, user_id, name, generation, lived_days, death_reason) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (1, 100, "Fallen Seth", 3, 7, "Starvation")
        )
        db.commit()
        cursor = db.execute("SELECT * FROM graveyard WHERE seth_id = 1")
        grave = cursor.fetchone()
        assert grave[2] == "Fallen Seth"
        assert grave[3] == 3
        assert grave[5] == "Starvation"
