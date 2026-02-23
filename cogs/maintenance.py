"""
Seth Maintenance - Feed and Heal your Seth (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands
import aiosqlite
import config
from config import (
    FEED_HUNGER_REDUCTION, HEAL_HEALTH_RESTORATION,
    TEST_DAMAGE_HEALTH, TEST_DAMAGE_HUNGER,
    MAX_HEALTH, MIN_HEALTH, MAX_HUNGER,
    HEALTH_CRITICAL_MAINT, HUNGER_STARVING_MAINT,
)
from utils.formatting import SethVisuals

class Maintenance(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = config.DATABASE_PATH

    @commands.command(name='feed')
    async def feed_seth(self, ctx: commands.Context) -> None:
        """Feed your Seth to reduce hunger (costs 1 food)"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT s.seth_id, s.name, s.hunger, r.food
                FROM seths s
                JOIN resources r ON s.user_id = r.user_id
                WHERE s.user_id = ? AND s.is_alive = 1""",
                (user_id,)
            )
            result = await cursor.fetchone()

            if not result:
                await ctx.send("💀 You don't have a living Seth to feed!")
                return

            seth_id, name, hunger, food = result

            if food < 1:
                embed = discord.Embed(
                    title="❌ No Food!",
                    description=f"You need food to feed {name}!\nUse `!mine` to gather resources.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            if hunger == 0:
                embed = discord.Embed(
                    title="😊 Not Hungry",
                    description=f"{name} is not hungry right now!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return

            new_hunger = max(0, hunger - FEED_HUNGER_REDUCTION)

            await db.execute(
                "UPDATE seths SET hunger = ? WHERE seth_id = ?",
                (new_hunger, seth_id)
            )
            await db.execute(
                "UPDATE resources SET food = food - 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

            hunger_display = SethVisuals.hunger_bar(new_hunger)

            embed = discord.Embed(
                title="🍖 Fed Seth!",
                description=f"{name} has been fed!",
                color=discord.Color.green()
            )
            embed.add_field(name="Stomach Status", value=hunger_display, inline=False)
            embed.add_field(name="Food Used", value="-1 🍖", inline=True)
            embed.add_field(name="Food Remaining", value=f"{food - 1} 🍖", inline=True)

            await ctx.send(embed=embed)

    @commands.command(name='heal')
    async def heal_seth(self, ctx: commands.Context) -> None:
        """Heal your Seth to increase health (costs 1 medicine)"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT s.seth_id, s.name, s.health, r.medicine
                FROM seths s
                JOIN resources r ON s.user_id = r.user_id
                WHERE s.user_id = ? AND s.is_alive = 1""",
                (user_id,)
            )
            result = await cursor.fetchone()

            if not result:
                await ctx.send("💀 You don't have a living Seth to heal!")
                return

            seth_id, name, health, medicine = result

            if medicine < 1:
                embed = discord.Embed(
                    title="❌ No Medicine!",
                    description=f"You need medicine to heal {name}!\nUse `!mine` to gather resources.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            if health == MAX_HEALTH:
                embed = discord.Embed(
                    title="💪 Full Health",
                    description=f"{name} is already at full health!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return

            new_health = min(MAX_HEALTH, health + HEAL_HEALTH_RESTORATION)

            await db.execute(
                "UPDATE seths SET health = ? WHERE seth_id = ?",
                (new_health, seth_id)
            )
            await db.execute(
                "UPDATE resources SET medicine = medicine - 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

            health_display = SethVisuals.health_bar(new_health, MAX_HEALTH)

            embed = discord.Embed(
                title="💊 Healed Seth!",
                description=f"{name} has been healed!",
                color=discord.Color.green()
            )
            embed.add_field(name="Health Status", value=health_display, inline=False)
            embed.add_field(name="Medicine Used", value="-1 💊", inline=True)
            embed.add_field(name="Medicine Remaining", value=f"{medicine - 1} 💊", inline=True)

            await ctx.send(embed=embed)

    @commands.command(name='damage')
    async def damage_test(self, ctx: commands.Context) -> None:
        """TEST COMMAND: Damage your Seth (cumulative damage for testing)"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT seth_id, name, health, hunger FROM seths WHERE user_id = ? AND is_alive = 1",
                (user_id,)
            )
            seth = await cursor.fetchone()

            if not seth:
                await ctx.send("💀 No living Seth to damage!")
                return

            seth_id, name, current_health, current_hunger = seth

            new_health = max(MIN_HEALTH, current_health - TEST_DAMAGE_HEALTH)
            new_hunger = min(MAX_HUNGER, current_hunger + TEST_DAMAGE_HUNGER)

            await db.execute(
                "UPDATE seths SET health = ?, hunger = ? WHERE seth_id = ?",
                (new_health, new_hunger, seth_id)
            )
            await db.commit()

            health_display = SethVisuals.health_bar(new_health, MAX_HEALTH)
            hunger_display = SethVisuals.hunger_bar(new_hunger)

            embed = discord.Embed(
                title="🔨 Test Damage Applied",
                description=f"{name} took damage!",
                color=discord.Color.orange()
            )
            embed.add_field(name="❤️ Health", value=health_display, inline=False)
            embed.add_field(name="🍖 Stomach", value=hunger_display, inline=False)
            embed.add_field(name="Damage Dealt", value=f"-{TEST_DAMAGE_HEALTH} health, +{TEST_DAMAGE_HUNGER} hunger", inline=False)

            if new_health <= HEALTH_CRITICAL_MAINT:
                embed.add_field(
                    name="⚠️ CRITICAL",
                    value="Seth is dying! Use !heal immediately!",
                    inline=False
                )
            elif new_hunger >= HUNGER_STARVING_MAINT:
                embed.add_field(
                    name="⚠️ STARVING",
                    value="Seth is starving! Use !feed immediately!",
                    inline=False
                )

            embed.set_footer(text="Use !feed and !heal to fix!")

            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Maintenance(bot))
