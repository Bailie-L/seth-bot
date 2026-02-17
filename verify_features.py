import os
import re

print("=" * 60)
print("FEATURE IMPLEMENTATION AUDIT")
print("=" * 60)

features = {
    "Premium Mining Cooldown": {
        "file": "cogs/economy.py",
        "pattern": r'(30.*if.*[Pp]remium|[Pp]remium.*30)',
        "critical": True
    },
    "Death Warnings": {
        "file": "cogs/decay.py", 
        "pattern": r'IMMINENT DEATH WARNING',
        "critical": True
    },
    "Trading System": {
        "file": "cogs/trading.py",
        "pattern": r'def trade',
        "critical": False
    },
    "Visual Bars": {
        "file": "utils/formatting.py",
        "pattern": r'[█░]',
        "critical": True
    },
    "120 Second Decay": {
        "file": "cogs/decay.py",
        "pattern": r'@tasks\.loop\(seconds=120\)',
        "critical": True
    },
    "Payment Integration": {
        "file": "cogs/",
        "pattern": r'(patreon|payment|webhook|stripe)',
        "critical": False
    },
    "Auto-feed Premium": {
        "file": "cogs/",
        "pattern": r'auto.*feed',
        "critical": False
    },
    "DM Support": {
        "file": "cogs/",
        "pattern": r'(create_dm|DMChannel)',
        "critical": False
    },
    "Multi-server Support": {
        "file": "database.py",
        "pattern": r'guild_id',
        "critical": False
    },
    "Cumulative Damage": {
        "file": "cogs/maintenance.py",
        "pattern": r'current_health.*-.*20',
        "critical": True
    }
}

for feature, check in features.items():
    found = False
    details = ""
    
    if os.path.isdir(check["file"]):
        # Search all files in directory
        for root, dirs, files in os.walk(check["file"]):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                        if re.search(check["pattern"], content, re.IGNORECASE):
                            found = True
                            match = re.search(check["pattern"], content, re.IGNORECASE)
                            details = f" (found in {file})"
                            break
    elif os.path.exists(check["file"]):
        with open(check["file"], 'r') as f:
            content = f.read()
            if re.search(check["pattern"], content, re.IGNORECASE):
                found = True
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if re.search(check["pattern"], line, re.IGNORECASE):
                        details = f" (line {i})"
                        break
    
    status = "✅" if found else "❌"
    priority = "CRITICAL" if check["critical"] else "Nice-to-have"
    print(f"{status} {feature}: {found}{details}")
    if not found and check["critical"]:
        print(f"   ⚠️ {priority} FEATURE MISSING!")

print("\n" + "=" * 60)
print("CODE QUALITY CHECKS")
print("=" * 60)

# Check for TODOs and debug code
todo_count = 0
print_count = 0
test_files = 0

for root, dirs, files in os.walk('cogs'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                todos = len(re.findall(r'TODO|FIXME|XXX|HACK', content, re.IGNORECASE))
                prints = len(re.findall(r'print\(', content))
                todo_count += todos
                print_count += prints
                if 'test' in file.lower():
                    test_files += 1

print(f"TODOs/FIXMEs in code: {todo_count}")
print(f"Debug print statements: {print_count}")
print(f"Test files in cogs: {test_files}")

# Check error handling
try_count = 0
bare_except = 0
for root, dirs, files in os.walk('cogs'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                try_count += len(re.findall(r'try:', content))
                bare_except += len(re.findall(r'except:(?!\s*#)', content))

print(f"Try/except blocks: {try_count}")
print(f"Bare excepts (bad practice): {bare_except}")

print("\n" + "=" * 60)
