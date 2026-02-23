"""
Seth Economy System - Mining and Resources (EMOJI FIX)
"""
import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime, timedelta
import random
import config
from config import (
    FOOD_MINE_MIN, FOOD_MINE_MAX,
    MEDICINE_MINE_MIN, MEDICINE_MINE_MAX,
    COAL_MINE_MIN, COAL_MINE_MAX,
)

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = config.DATABASE_PATH
        self.cooldowns: dict[int, datetime] = {}
        self.food_emoji = "🍖"
        self.medicine_emoji = "💊"
        self.coal_emoji = "⚫"
        self.star_emoji = "⭐"

    @commands.command(name='mine')
    async def mine(self, ctx: commands.Context) -> None:
        """Mine for resources with cooldown"""
        user_id = ctx.author.id

        # Check if user has Premium role
        premium_role = discord.utils.get(ctx.guild.roles, name="Premium")
        is_premium = premium_role in ctx.author.roles if premium_role else False
        cooldown_seconds = config.PREMIUM_MINE_COOLDOWN if is_premium else config.MINE_COOLDOWN

        # Check cooldown
        if user_id in self.cooldowns:
            time_diff = datetime.now() - self.cooldowns[user_id]
            if time_diff < timedelta(seconds=cooldown_seconds):
                remaining = cooldown_seconds - int(time_diff.total_seconds())
                premium_msg = f" {self.star_emoji} (Premium: {config.PREMIUM_MINE_COOLDOWN}s cooldown)" if is_premium else ""
                await ctx.send(f"⏳ **Mining Cooldown**\nYou must wait **{remaining} seconds** before mining again!{premium_msg}")
                return

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM seths WHERE user_id = ? AND is_alive = 1",
                (user_id,)
            )
            seth = await cursor.fetchone()

            if not seth:
                await ctx.send("❌ You need a living Seth to mine! Use `!start [name]`")
                return

            seth_name = seth[0]

            food = random.randint(FOOD_MINE_MIN, FOOD_MINE_MAX)
            medicine = random.randint(MEDICINE_MINE_MIN, MEDICINE_MINE_MAX)
            coal = random.randint(COAL_MINE_MIN, COAL_MINE_MAX)

            await db.execute(
                """INSERT OR REPLACE INTO resources (user_id, food, medicine, coal)
                VALUES (?,
                    COALESCE((SELECT food FROM resources WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT medicine FROM resources WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT coal FROM resources WHERE user_id = ?), 0) + ?)""",
                (user_id, user_id, food, user_id, medicine, user_id, coal)
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT food, medicine, coal FROM resources WHERE user_id = ?",
                (user_id,)
            )
            totals = await cursor.fetchone()

            self.cooldowns[user_id] = datetime.now()

            embed = discord.Embed(
                title="⛏️ Mining Complete!",
                description=f"{seth_name} gathered resources!",
                color=0x8B4513
            )

            found_str = f"{self.food_emoji} Food: +{food}   {self.medicine_emoji} Medicine: +{medicine}   {self.coal_emoji} Coal: +{coal}"
            embed.add_field(name="Found", value=found_str, inline=False)

            inv_str = f"{self.food_emoji} {totals[0]}   {self.medicine_emoji} {totals[1]}   {self.coal_emoji} {totals[2]}"
            embed.add_field(name="Total Inventory", value=inv_str, inline=False)

            cooldown_msg = f"Next mine in {cooldown_seconds} seconds"
            if is_premium:
                cooldown_msg = f"{cooldown_msg} {self.star_emoji} (Premium bonus!)"
            embed.set_footer(text=cooldown_msg)

            await ctx.send(embed=embed)

    @commands.command(name='inventory', aliases=['inv'])
    async def inventory(self, ctx: commands.Context) -> None:
        """Check your resources"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT food, medicine, coal FROM resources WHERE user_id = ?",
                (user_id,)
            )
            resources = await cursor.fetchone()

            if not resources:
                await ctx.send("📦 You have no resources! Use `!mine` to gather some.")
                return

            embed = discord.Embed(
                title="📦 Your Inventory",
                color=0x4CAF50
            )

            embed.add_field(name=f"{self.food_emoji} Food", value=str(resources[0]), inline=True)
            embed.add_field(name=f"{self.medicine_emoji} Medicine", value=str(resources[1]), inline=True)
            embed.add_field(name=f"{self.coal_emoji} Coal", value=str(resources[2]), inline=True)

            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))
