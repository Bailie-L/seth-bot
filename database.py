"""
Seth Bot Database
Handles all database operations with aiosqlite
"""
import aiosqlite
import os
from config import DATABASE_PATH, DEFAULT_RELATIONSHIP_SCORE

async def init_db() -> None:
    """Initialize database with all required tables"""
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                discord_name TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Seths table - the core entities
        await db.execute('''
            CREATE TABLE IF NOT EXISTS seths (
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
                parent_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (parent_id) REFERENCES seths(seth_id)
            )
        ''')
        
        # Resources table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                user_id INTEGER PRIMARY KEY,
                food INTEGER DEFAULT 5,
                medicine INTEGER DEFAULT 2,
                coal INTEGER DEFAULT 0,
                last_mine_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Graveyard table - memorial for dead Seths
        await db.execute('''
            CREATE TABLE IF NOT EXISTS graveyard (
                seth_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                generation INTEGER,
                lived_days INTEGER,
                death_reason TEXT,
                death_time TIMESTAMP,
                memorial_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        await db.commit()
        print("✅ Database initialized with all tables!")

async def test_connection() -> bool:
    """Test database connection"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = await cursor.fetchall()
            print(f"📊 Found {len(tables)} tables: {[t[0] for t in tables]}")
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    # Test database when run directly
    import asyncio
    asyncio.run(init_db())
    asyncio.run(test_connection())

async def create_drama_tables() -> None:
    """Create NPC relationship tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # NPC relationship matrix
        await db.execute('''
            CREATE TABLE IF NOT EXISTS npc_relationships (
                npc1 TEXT NOT NULL,
                npc2 TEXT NOT NULL,
                relationship_type TEXT DEFAULT 'neutral',
                relationship_score INTEGER DEFAULT 50,
                last_event TEXT,
                last_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (npc1, npc2)
            )
        ''')
        
        # Current NPC states (dating, fighting, etc)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS npc_states (
                npc_name TEXT PRIMARY KEY,
                current_mood TEXT DEFAULT 'normal',
                dating TEXT,
                rival TEXT,
                health INTEGER DEFAULT 100,
                location TEXT DEFAULT 'village_square'
            )
        ''')
        
        # Drama history
        await db.execute('''
            CREATE TABLE IF NOT EXISTS drama_history (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                npc1 TEXT,
                npc2 TEXT,
                player_votes_option1 INTEGER DEFAULT 0,
                player_votes_option2 INTEGER DEFAULT 0,
                player_votes_option3 INTEGER DEFAULT 0,
                outcome TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Player drama participation
        await db.execute('''
            CREATE TABLE IF NOT EXISTS player_drama (
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                vote_choice INTEGER,
                seth_involved BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, event_id)
            )
        ''')
        
        await db.commit()
        
        # Initialize NPCs if not exists
        npcs = ['Luna', 'Marcus', 'Felix', 'Aria', 'Thorne']
        for npc in npcs:
            await db.execute('''
                INSERT OR IGNORE INTO npc_states (npc_name) VALUES (?)
            ''', (npc,))
        
        # Initialize relationships
        for i, npc1 in enumerate(npcs):
            for npc2 in npcs[i+1:]:
                await db.execute('''
                    INSERT OR IGNORE INTO npc_relationships (npc1, npc2)
                    VALUES (?, ?)
                ''', (npc1, npc2))
        
        await db.commit()
        print("✅ Drama tables initialized with NPCs!")

