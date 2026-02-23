"""
Seth Bot - Main Bot File
A Discord Tamagotchi with permanent death
"""
import discord
from discord.ext import commands
from datetime import datetime
import config
import database

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=config.BOT_PREFIX,
    intents=intents,
    help_command=None  # We'll make custom help
)

@bot.event
async def on_ready():
    """Bot startup event"""
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('🤖 Seth Bot is ALIVE!')
    print(f'👤 Logged in as: {bot.user.name}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'🌍 Servers: {len(bot.guilds)}')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    # Initialize database
    await database.init_db()

    # Load cogs
    try:
        await bot.load_extension('cogs.seth_core')
        print('✅ Seth Core system loaded!')
        await bot.load_extension('cogs.economy')
        print('✅ Economy system loaded!')
        await bot.load_extension('cogs.maintenance')
        print('✅ Maintenance system loaded!')
        await bot.load_extension('cogs.decay')
        print("✅ Decay system loaded!")
        await bot.load_extension("cogs.leaderboard")
        print("✅ Leaderboard system loaded!")
        await bot.load_extension("cogs.public")
        print("✅ Public features loaded!")
        await bot.load_extension("cogs.trading")
        print("✅ Trading system loaded!")
        await bot.load_extension("cogs.drama")
        print("✅ Drama engine loaded!")
        await bot.load_extension("cogs.help")
        print("✅ Help system loaded!")
    except Exception as e:
        print(f"❌ Failed to load cogs: {e}")

    # Set bot status
    await bot.change_presence(
        activity=discord.Game(name=f"{config.BOT_PREFIX}help | Raising Seths")
    )

@bot.command(name='ping')
async def ping(ctx):
    """Test command to verify bot is working"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** {latency}ms\n**Status:** Seth Bot is operational!",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name='test')
async def test(ctx):
    """Test database connection"""
    if await database.test_connection():
        await ctx.send("✅ **Database is working!** Seth births can begin...")
    else:
        await ctx.send("❌ **Database error!** Check console for details.")

@bot.command(name='testemoji')
async def testemoji(ctx):
    """Test emoji rendering in different contexts"""
    food = "🍖"
    medicine = "💊"
    coal = "⚫"

    # Test 1: Direct message
    await ctx.send(f"Direct: {food} Food {medicine} Medicine {coal} Coal")

    # Test 2: Embed description
    embed = discord.Embed(
        title="Test Embed",
        description=f"{food} Food {medicine} Medicine {coal} Coal"
    )
    await ctx.send(embed=embed)

    # Test 3: Embed field value (like economy.py)
    embed2 = discord.Embed(title="Field Test")
    embed2.add_field(
        name="Resources",
        value=f"{food} Food: 10   {medicine} Medicine: 5   {coal} Coal: 20",
        inline=False
    )
    await ctx.send(embed=embed2)

    # Test 4: Discord shortcodes
    await ctx.send("Testing Discord shortcodes:")
    await ctx.send(":meat_on_bone: :pill: :black_circle: :star:")

    embed3 = discord.Embed(title="Shortcode Test")
    embed3.add_field(
        name="Resources",
        value=":meat_on_bone: Food: 10   :pill: Medicine: 5   :black_circle: Coal: 20",
        inline=False
    )
    await ctx.send(embed=embed3)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❓ Unknown command. Use `{config.BOT_PREFIX}help` for commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing arguments! Check `{config.BOT_PREFIX}help {ctx.command}`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found! Make sure to mention them with @")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument! Check the command usage.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ You don't have permission to use this command!")
    else:
        print(f"Error: {error}")
        await ctx.send("💀 Something went wrong! The Seth gods are displeased...")

if __name__ == "__main__":
    config.verify_token()
    bot.run(config.DISCORD_TOKEN)
