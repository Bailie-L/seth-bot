"""
Seth Leaderboard System - Track longest living Seths (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands
import aiosqlite
import config
from datetime import datetime, timedelta
from config import SECONDS_PER_HOUR, SECONDS_PER_DAY
from utils.formatting import SethVisuals

class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = config.DATABASE_PATH

    @commands.command(name='top')
    async def top_seths(self, ctx: commands.Context) -> None:
        """Show longest living Seths"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT name, generation, death_time, user_id
                FROM graveyard
                ORDER BY death_time DESC
                LIMIT 10"""
            )
            top_dead = await cursor.fetchall()

            if not top_dead:
                await ctx.send("📊 No Seths have died yet!")
                return

            seths_with_times = []
            max_lifespan = 0

            for name, gen, death_time, user_id in top_dead:
                cursor2 = await db.execute(
                    """SELECT birth_time FROM seths
                    WHERE name = ? AND user_id = ? AND is_alive = 0
                    LIMIT 1""",
                    (name, user_id)
                )
                birth_data = await cursor2.fetchone()
                if birth_data:
                    birth_time = birth_data[0]
                else:
                    birth_time = (datetime.fromisoformat(death_time) - timedelta(minutes=1)).isoformat()

                lifespan_seconds = (datetime.fromisoformat(death_time) - datetime.fromisoformat(birth_time)).total_seconds()
                max_lifespan = max(max_lifespan, lifespan_seconds)
                seths_with_times.append((name, gen, birth_time, death_time, user_id, lifespan_seconds))

            seths_with_times.sort(key=lambda x: x[5], reverse=True)

            embed = discord.Embed(
                title="🏆 **Longest Living Seths**",
                description="The legends who lived longest:",
                color=0xFFD700
            )

            for i, (name, gen, birth_time, death_time, user_id, lifespan_seconds) in enumerate(seths_with_times[:10], 1):
                user = self.bot.get_user(user_id)
                username = user.name if user else "Unknown"

                if lifespan_seconds < SECONDS_PER_HOUR:
                    minutes = int(lifespan_seconds / 60)
                    time_display = f"{minutes} minutes"
                elif lifespan_seconds < SECONDS_PER_DAY:
                    hours = round(lifespan_seconds / SECONDS_PER_HOUR, 1)
                    time_display = f"{hours} hours"
                else:
                    days = round(lifespan_seconds / SECONDS_PER_DAY, 1)
                    time_display = f"{days} days"

                if max_lifespan > 0:
                    relative_percentage = (lifespan_seconds / max_lifespan) * 100
                    lifespan_bar = SethVisuals.resource_bar(int(relative_percentage), 100)
                else:
                    lifespan_bar = SethVisuals.resource_bar(0, 100)

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

                embed.add_field(
                    name=f"{medal} **{name}** (Gen {gen})",
                    value=f"{lifespan_bar}\nLived **{time_display}** | Owner: {username}",
                    inline=False
                )

            embed.set_footer(text="Bars show relative lifespan compared to #1")
            await ctx.send(embed=embed)

    @commands.command(name='generations')
    async def top_generations(self, ctx: commands.Context) -> None:
        """Show highest generation Seths"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT name, generation, is_alive, user_id
                FROM seths
                ORDER BY generation DESC, seth_id DESC
                LIMIT 10"""
            )
            top_gens = await cursor.fetchall()

            if not top_gens:
                await ctx.send("📊 No Seths exist yet!")
                return

            embed = discord.Embed(
                title="🧬 **Highest Generation Seths**",
                description="The longest bloodlines:",
                color=0x9B59B6
            )

            max_gen = top_gens[0][1] if top_gens else 1

            for i, (name, gen, is_alive, user_id) in enumerate(top_gens, 1):
                user = self.bot.get_user(user_id)
                username = user.name if user else "Unknown"

                gen_bar = SethVisuals.resource_bar(gen, max_gen)

                status = "🟢 ALIVE" if is_alive else "💀 DEAD"
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

                embed.add_field(
                    name=f"{medal} **{name}** - Generation {gen}",
                    value=f"{gen_bar}\nStatus: {status} | Owner: {username}",
                    inline=False
                )

            embed.set_footer(text="Higher generations mean longer family lines!")
            await ctx.send(embed=embed)

    @commands.command(name='mystats')
    async def my_stats(self, ctx: commands.Context) -> None:
        """Show your personal Seth statistics"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT name, generation, health, hunger
                FROM seths WHERE user_id = ? AND is_alive = 1""",
                (user_id,)
            )
            current = await cursor.fetchone()

            cursor = await db.execute(
                "SELECT COUNT(*) FROM seths WHERE user_id = ?",
                (user_id,)
            )
            total_seths = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT MAX(generation) FROM seths WHERE user_id = ?",
                (user_id,)
            )
            max_gen = (await cursor.fetchone())[0] or 0

            cursor = await db.execute(
                "SELECT food, medicine, coal FROM resources WHERE user_id = ?",
                (user_id,)
            )
            resources = await cursor.fetchone()

            embed = discord.Embed(
                title=f"📊 **{ctx.author.name}'s Seth Statistics**",
                color=discord.Color.blue()
            )

            if current:
                name, gen, health, hunger = current
                health_bar = SethVisuals.health_bar(health, 100)
                hunger_bar = SethVisuals.hunger_bar(hunger)

                embed.add_field(
                    name="🎮 Current Seth",
                    value=f"**{name}** (Gen {gen})\nHealth: {health_bar}\nStomach: {hunger_bar}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎮 Current Seth",
                    value="💀 No living Seth! Use `!start [name]` to create one.",
                    inline=False
                )

            embed.add_field(name="📈 Total Seths", value=f"**{total_seths}** created", inline=True)
            embed.add_field(name="🧬 Highest Gen", value=f"Generation **{max_gen}**", inline=True)

            if resources:
                food, medicine, coal = resources
                embed.add_field(
                    name="📦 Resources",
                    value=f"🍖 Food: **{food}** | 💊 Medicine: **{medicine}** | ⚫ Coal: **{coal}**",
                    inline=False
                )

            await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))
