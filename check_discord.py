import os

print("=" * 60)
print("DISCORD BOT RUNTIME AUDIT")
print("=" * 60)

# Check .env file (without exposing token)
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        lines = f.readlines()
        print("📋 Environment Variables:")
        for line in lines:
            if 'TOKEN' in line:
                print("  ✅ Discord token configured")
            elif '=' in line:
                key = line.split('=')[0]
                print(f"  - {key} configured")
else:
    print("❌ .env file missing!")

# Check config.py
print("\n⚙️ Configuration Settings:")
if os.path.exists('config.py'):
    with open('config.py', 'r') as f:
        content = f.read()
        if 'PREMIUM_MINE_COOLDOWN' in content:
            print("  ✅ Premium cooldowns configured")
        if 'DECAY_INTERVAL' in content or '120' in content:
            print("  ✅ Decay interval configured")
        if 'STARTING_HEALTH' in content:
            print("  ✅ Starting stats configured")

# Check which cogs are loaded
print("\n🔌 Cogs Loaded in bot.py:")
if os.path.exists('bot.py'):
    with open('bot.py', 'r') as f:
        content = f.read()
        import re
        cogs = re.findall(r'load_extension\(["\']cogs\.(\w+)["\']\)', content)
        for cog in cogs:
            print(f"  - {cog}")
        print(f"  Total: {len(cogs)} cogs")

# Check for required Discord permissions
print("\n🔐 Required Permissions Check:")
required = ['send_messages', 'embed_links', 'add_reactions', 'manage_messages', 'read_message_history']
print("  Bot needs:", ', '.join(required))

# Check requirements.txt
print("\n📦 Dependencies:")
if os.path.exists('requirements.txt'):
    with open('requirements.txt', 'r') as f:
        deps = f.readlines()
        critical = ['discord.py', 'aiosqlite', 'python-dotenv']
        for c in critical:
            found = any(c in dep for dep in deps)
            status = "✅" if found else "❌"
            print(f"  {status} {c}")

print("\n" + "=" * 60)
print("DEPLOYMENT READINESS ASSESSMENT")
print("=" * 60)

readiness = {
    "Core Gameplay": 90,  # Works but single-user only
    "Multi-user Support": 0,  # Never tested
    "Payment System": 0,  # Not implemented
    "Production Hardening": 20,  # SQLite, no backups
    "Documentation": 60,  # Help system exists
    "Testing Coverage": 10,  # Single user only
}

total = sum(readiness.values()) / len(readiness)
for feature, score in readiness.items():
    bar = "█" * (score // 10) + "░" * ((100 - score) // 10)
    print(f"{feature:.<25} {bar} {score}%")

print(f"\nOVERALL READINESS: {total:.0f}%")

if total < 50:
    print("⚠️ NOT READY FOR PRODUCTION")
    print("\nCRITICAL MISSING:")
    print("1. Multi-user testing")
    print("2. Payment integration") 
    print("3. Production database")
    print("4. Backup system")
    print("5. Error recovery")

print("\n" + "=" * 60)
