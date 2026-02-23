"""
Seth Core System - Birth, Life, Death (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime
import config
from config import (
    MAX_HEALTH,
    HEALTH_CRITICAL_STATUS, HUNGER_CRITICAL_STATUS,
    HEALTH_WARNING_STATUS, HUNGER_WARNING_STATUS,
)
from utils.formatting import SethVisuals
from utils.status import get_health_status, get_hunger_status, get_health_color

class SethCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = config.DATABASE_PATH

    @commands.command(name='start')
    async def start_seth(self, ctx, *, name: str = None):
        """Create your first Seth or continue bloodline"""
        user_id = ctx.author.id

        # Check if user already has a living Seth
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT name, generation FROM seths WHERE user_id = ? AND is_alive = 1",
                (user_id,)
            )
            existing = await cursor.fetchone()

            if existing:
                embed = discord.Embed(
                    title="❌ You already have a Seth!",
                    description=f"**{existing[0]}** (Gen {existing[1]}) is still alive!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Create new user if needed
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, discord_name) VALUES (?, ?)",
                (user_id, str(ctx.author))
            )

            # Initialize resources for new user
            await db.execute(
                "INSERT OR IGNORE INTO resources (user_id) VALUES (?)",
                (user_id,)
            )

            # Get generation number (check for dead parent)
            cursor = await db.execute(
                "SELECT MAX(generation) FROM seths WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            generation = (result[0] + 1) if result[0] else 1

            # Name the Seth
            seth_name = f"{name} Seth" if name else "Seth Jr."

            # Create the Seth!
            await db.execute(
                """INSERT INTO seths
                (user_id, name, generation, health, hunger, is_alive)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, seth_name, generation, config.STARTING_HEALTH,
                 config.STARTING_HUNGER, 1)
            )
            await db.commit()

            # Birth announcement with standardized display
            embed = discord.Embed(
                title="🎉 A SETH IS BORN!",
                description=f"**{seth_name}** (Generation {generation}) has entered the world!",
                color=discord.Color.green()
            )

            # Use standardized visual bars
            health_display = SethVisuals.health_bar(config.STARTING_HEALTH, MAX_HEALTH)
            hunger_display = SethVisuals.hunger_bar(config.STARTING_HUNGER)

            embed.add_field(name="❤️ Health", value=health_display, inline=False)
            embed.add_field(name="🍖 Stomach", value=hunger_display, inline=False)
            embed.add_field(name="🧬 Generation", value=generation, inline=True)
            embed.set_footer(text=f"Parent: {ctx.author.name} | Use !status to check on your Seth")

            await ctx.send(embed=embed)

    @commands.command(name='status')
    async def status(self, ctx):
        """Check your Seth's vital signs"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            # Get Seth data
            cursor = await db.execute(
                """SELECT name, generation, health, hunger, birth_time
                FROM seths WHERE user_id = ? AND is_alive = 1""",
                (user_id,)
            )
            seth = await cursor.fetchone()

            if not seth:
                embed = discord.Embed(
                    title="💀 No Living Seth",
                    description=f"You don't have a Seth! Use `{config.BOT_PREFIX}start [name]` to create one!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            name, gen, health, hunger, birth_time = seth

            # Get status text for health and hunger
            health_status = get_health_status(health)
            hunger_status = get_hunger_status(hunger)

            # Use standardized visual bars
            health_display = SethVisuals.health_bar(health, MAX_HEALTH)
            hunger_display = SethVisuals.hunger_bar(hunger)

            # Calculate age
            birth = datetime.fromisoformat(birth_time)
            age = (datetime.utcnow() - birth).days

            # Status embed
            embed = discord.Embed(
                title=f"📊 {name} Status",
                color=get_health_color(health)
            )

            # Standardized health display
            embed.add_field(
                name="❤️ Health",
                value=f"{health_display} [{health_status}]",
                inline=False
            )

            # Standardized stomach display
            embed.add_field(
                name="🍖 Stomach",
                value=f"{hunger_display} [{hunger_status}]",
                inline=False
            )

            embed.add_field(name="🧬 Generation", value=gen, inline=True)
            embed.add_field(name="📅 Age", value=f"{age} days", inline=True)

            # Critical warning messages with clear instructions
            if health < HEALTH_CRITICAL_STATUS or hunger > HUNGER_CRITICAL_STATUS:
                embed.add_field(
                    name="🚨 **CRITICAL WARNING** 🚨",
                    value="**Wake up ass-hole, I'm starving!!! Feed me now!**",
                    inline=False
                )
                # Add specific action needed based on what's critical
                if health < HEALTH_CRITICAL_STATUS and hunger > HUNGER_CRITICAL_STATUS:
                    embed.add_field(
                        name="💀 BOTH CRITICAL",
                        value="Use `!heal` for health AND `!feed` for hunger NOW!",
                        inline=False
                    )
                elif hunger > HUNGER_CRITICAL_STATUS:
                    embed.add_field(
                        name="💀 ACTION REQUIRED",
                        value="Use `!feed` immediately to reduce hunger!",
                        inline=False
                    )
                elif health < HEALTH_CRITICAL_STATUS:
                    embed.add_field(
                        name="💀 ACTION REQUIRED",
                        value="Use `!heal` immediately to increase health!",
                        inline=False
                    )
            elif health < HEALTH_WARNING_STATUS:
                embed.add_field(name="⚠️ WARNING", value="Seth's health is getting low! Use `!heal`", inline=False)
            elif hunger > HUNGER_WARNING_STATUS:
                embed.add_field(name="⚠️ WARNING", value="Seth is getting hungry! Use `!feed`", inline=False)

            await ctx.send(embed=embed)

    async def announce_death(self, ctx, seth_name, generation, cause="Natural causes"):
        """Announce death in #seth-graveyard channel"""
        graveyard_channel = discord.utils.get(ctx.guild.channels, name="seth-graveyard")
        if graveyard_channel:
            embed = discord.Embed(
                title="💀 SETH HAS DIED!",
                description=f"**{seth_name}** (Generation {generation}) has passed away",
                color=0x000000
            )
            embed.add_field(name="Cause of Death", value=cause, inline=False)
            embed.add_field(name="Owner", value=ctx.author.mention, inline=False)
            embed.set_footer(text="Press F to pay respects")
            msg = await graveyard_channel.send(embed=embed)
            await msg.add_reaction("🇫")

    @commands.command(name="kill")
    async def kill_seth(self, ctx):
        """TEST COMMAND: Kill your Seth instantly"""
        user_id = ctx.author.id

        async with aiosqlite.connect(self.db_path) as db:
            # Get living Seth
            cursor = await db.execute(
                """SELECT seth_id, name, generation, birth_time
                FROM seths WHERE user_id = ? AND is_alive = 1""",
                (user_id,)
            )
            seth = await cursor.fetchone()

            if not seth:
                await ctx.send("💀 You don't have a living Seth to kill!")
                return

            seth_id, name, gen, birth_time = seth

            # Calculate lifespan
            birth = datetime.fromisoformat(birth_time)
            lived_days = (datetime.utcnow() - birth).days

            # Kill the Seth
            death_time = datetime.utcnow()
            await db.execute(
                """UPDATE seths
                SET is_alive = 0, death_time = ?, death_reason = ?
                WHERE seth_id = ?""",
                (death_time, "Murdered by owner (test)", seth_id)
            )

            # Add to graveyard
            # Announce death publicly
            await self.announce_death(ctx, name, gen, "Murdered by owner")
            await db.execute(
                """INSERT INTO graveyard
                (seth_id, user_id, name, generation, lived_days, death_reason, death_time, memorial_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (seth_id, user_id, name, gen, lived_days, "Murdered by owner (test)",
                 death_time, f"Here lies {name}, cruelly murdered for testing.")
            )

            await db.commit()

            # Death announcement
            embed = discord.Embed(
                title="💀 SETH HAS DIED!",
                description=f"**{name}** (Generation {gen}) has been murdered!",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="⏰ Lived", value=f"{lived_days} days", inline=True)
            embed.add_field(name="☠️ Cause", value="Murdered by owner", inline=True)
            embed.add_field(name="🪦 Legacy", value=f"Generation {gen} has ended", inline=True)
            embed.set_footer(text=f"Use {config.BOT_PREFIX}start [name] to continue the bloodline")

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SethCore(bot))
