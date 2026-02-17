import discord
from discord.ext import commands
import asyncio

# Test bot to verify emoji rendering
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def testemoji(ctx):
    """Test emoji rendering in different contexts"""
    # Direct emojis
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
    
    # Test 4: Raw unicode
    embed3 = discord.Embed(title="Unicode Test")
    embed3.add_field(
        name="Raw Unicode",
        value="\U0001f356 Food \U0001f48a Medicine \u26ab Coal",
        inline=False
    )
    await ctx.send(embed=embed3)

# Run this test with your bot token
print("Add this command to your bot.py temporarily to test")
