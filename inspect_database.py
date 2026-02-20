import sqlite3
import os

print("=" * 60)
print("PROJECT SETH DATABASE AUDIT")
print("=" * 60)

db_path = 'data/seth.db'
if not os.path.exists(db_path):
    print("❌ Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"\n📋 Tables found: {len(tables)}")
for table in tables:
    print(f"  - {table[0]}")

# User statistics
cursor.execute("SELECT COUNT(DISTINCT user_id) FROM seths")
unique_users = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM seths")
total_seths = cursor.fetchone()[0]
print("\n👤 USER TESTING REALITY:")
print(f"  Unique users who created Seths: {unique_users}")
print(f"  Total Seths created: {total_seths}")
if unique_users == 1:
    print("  ⚠️ SINGLE USER TESTING ONLY - Multi-user claims are FALSE")

# Check current living Seths
cursor.execute("SELECT name, generation, health, hunger FROM seths WHERE is_alive = 1")
living = cursor.fetchall()
print(f"\n🎮 Living Seths: {len(living)}")
for seth in living:
    print(f"  - {seth[0]} (Gen {seth[1]}): Health={seth[2]}, Hunger={seth[3]}")

# Death records
cursor.execute("SELECT COUNT(*) FROM graveyard")
deaths = cursor.fetchone()[0]
print(f"\n💀 Total deaths recorded: {deaths}")

# Check highest generation (proves gameplay depth)
cursor.execute("SELECT MAX(generation) FROM seths")
max_gen = cursor.fetchone()[0]
print(f"📈 Highest generation reached: {max_gen or 0}")

# Check for premium users
cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
premium = cursor.fetchone()[0]
print(f"\n💰 Premium users: {premium}")
if premium == 0:
    print("  ⚠️ NO PREMIUM TESTING - Payment features untested")

# Check if NPC tables exist (Drama system from Days 8-14)
try:
    cursor.execute("SELECT COUNT(*) FROM npc_relationships")
    npc_count = cursor.fetchone()[0]
    print("\n🎭 NPC Drama System:")
    print(f"  Relationships: {npc_count}")
except Exception:
    print("\n🎭 NPC Drama System: ❌ TABLES DON'T EXIST")
    print("  ⚠️ Drama system claims appear FALSE")

# Check resources to see mining activity
cursor.execute("SELECT user_id, food, medicine, coal FROM resources")
resources = cursor.fetchall()
print("\n⛏️ Resource holdings:")
for r in resources:
    print(f"  User {r[0]}: Food={r[1]}, Medicine={r[2]}, Coal={r[3]}")

# Timeline check - when was first Seth created?
cursor.execute("SELECT MIN(birth_time) FROM seths")
first_birth = cursor.fetchone()[0]
if first_birth:
    print(f"\n⏰ First Seth created: {first_birth}")
    print("  Project age: Only TODAY's data")

conn.close()
print("\n" + "=" * 60)
print("AUDIT COMPLETE - Check claims vs reality")
print("=" * 60)
