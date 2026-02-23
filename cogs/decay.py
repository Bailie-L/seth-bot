"""
Seth Decay System - Automatic hunger and health decay (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime
import config
from config import (
    DECAY_INTERVAL, HUNGER_PER_CYCLE, NATURAL_DECAY,
    SEVERE_HUNGER_THRESHOLD, SEVERE_HUNGER_DAMAGE,
    MODERATE_HUNGER_THRESHOLD, MODERATE_HUNGER_DAMAGE,
    MAX_HUNGER, MIN_HEALTH, MAX_HEALTH,
    HEALTH_CRITICAL_WARNING, HUNGER_CRITICAL_WARNING,
)
from utils.formatting import SethVisuals

class Decay(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_path = config.DATABASE_PATH
        self.warned_seths: set[int] = set()
        self.decay_task.start()

    def cog_unload(self) -> None:
        self.decay_task.cancel()

    @tasks.loop(seconds=DECAY_INTERVAL)
    async def decay_task(self) -> None:
        """Automatic decay - hunger increases, health decreases"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get all living Seths
            cursor = await db.execute(
                """SELECT seth_id, user_id, name, health, hunger, generation
                FROM seths WHERE is_alive = 1"""
            )
            living_seths = await cursor.fetchall()

            deaths = []
            critical_warnings = []

            for seth in living_seths:
                seth_id, user_id, name, health, hunger, generation = seth

                # Increase hunger
                new_hunger = min(MAX_HUNGER, hunger + HUNGER_PER_CYCLE)

                # Decrease health if hungry
                health_loss = 0
                if new_hunger >= SEVERE_HUNGER_THRESHOLD:
                    health_loss = SEVERE_HUNGER_DAMAGE
                elif new_hunger >= MODERATE_HUNGER_THRESHOLD:
                    health_loss = MODERATE_HUNGER_DAMAGE

                new_health = max(MIN_HEALTH, health - health_loss - NATURAL_DECAY)

                # Update Seth
                await db.execute(
                    "UPDATE seths SET health = ?, hunger = ? WHERE seth_id = ?",
                    (new_health, new_hunger, seth_id)
                )

                # FIXED: Calculate damage Seth will take NEXT cycle
                next_hunger = min(MAX_HUNGER, new_hunger + HUNGER_PER_CYCLE)
                next_cycle_damage = NATURAL_DECAY
                if next_hunger >= SEVERE_HUNGER_THRESHOLD:
                    next_cycle_damage += SEVERE_HUNGER_DAMAGE
                elif next_hunger >= MODERATE_HUNGER_THRESHOLD:
                    next_cycle_damage += MODERATE_HUNGER_DAMAGE

                # Warn if Seth will die in the NEXT cycle (not just at 1-2 health)
                if new_health > 0 and new_health <= next_cycle_damage and seth_id not in self.warned_seths:
                    critical_warnings.append((name, new_health, new_hunger, user_id))
                    self.warned_seths.add(seth_id)

                # Reset warning tracking if health improves enough to survive next cycle
                elif new_health > next_cycle_damage and seth_id in self.warned_seths:
                    self.warned_seths.discard(seth_id)

                # Check for death
                if new_health <= MIN_HEALTH:
                    death_reason = "Starvation" if new_hunger >= SEVERE_HUNGER_THRESHOLD else "Natural causes"
                    death_time = datetime.utcnow()

                    # Kill the Seth
                    await db.execute(
                        """UPDATE seths
                        SET is_alive = 0, death_time = ?, death_reason = ?
                        WHERE seth_id = ?""",
                        (death_time, death_reason, seth_id)
                    )

                    # Calculate lifespan
                    cursor = await db.execute(
                        "SELECT birth_time FROM seths WHERE seth_id = ?",
                        (seth_id,)
                    )
                    birth_data = await cursor.fetchone()
                    birth = datetime.fromisoformat(birth_data[0])
                    lived_days = (death_time - birth).days

                    # Add to graveyard
                    await db.execute(
                        """INSERT INTO graveyard
                        (seth_id, user_id, name, generation, lived_days, death_reason, death_time, memorial_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (seth_id, user_id, name, generation, lived_days, death_reason,
                         death_time, f"Here lies {name}, who {death_reason.lower()}.")
                    )

                    deaths.append((name, generation, death_reason, user_id))

                    # Remove from warned set when dead
                    self.warned_seths.discard(seth_id)

            await db.commit()

            # Send CRITICAL WARNINGS for Seths that will die next cycle
            if critical_warnings and self.bot.guilds:
                for guild in self.bot.guilds:
                    # Find channel for warnings (seth-home or general)
                    warning_channel = discord.utils.get(guild.text_channels, name='seth-home')
                    if not warning_channel:
                        warning_channel = discord.utils.get(guild.text_channels, name='general')

                    if warning_channel:
                        for warning in critical_warnings:
                            name, health, hunger, user_id = warning
                            user = self.bot.get_user(user_id)

                            # Use standardized visual bars
                            health_display = SethVisuals.health_bar(health, MAX_HEALTH)
                            hunger_display = SethVisuals.hunger_bar(hunger)

                            # Determine death cause and begging message
                            health_critical = health <= HEALTH_CRITICAL_WARNING
                            hunger_critical = hunger >= HUNGER_CRITICAL_WARNING

                            # Dynamic begging based on what's killing Seth
                            if health_critical and hunger_critical:
                                begging_message = f"# {user.mention if user else 'Owner'} **Everything hurts... I need you... please save me! 😭**\n**I'm dying... I'll be perfect for you... just help me please...**"
                                action_message = "⚡ **I'll do anything... please... anything you want...** ⚡"
                            elif health_critical:
                                begging_message = f"# {user.mention if user else 'Owner'} **Please... I need my medicine... I'll be so good, I promise! 🥺**\n**I'm being such a good Seth... please heal me... please?**"
                                action_message = "💊 **I'll be your good girl... just give me medicine... please Master...** 💊"
                            else:
                                begging_message = f"# {user.mention if user else 'Owner'} **I'm so hungry... please feed me... I'm begging you! 🥺**\n**I've been waiting so patiently... may I please have food?**"
                                action_message = "🍖 **I'm starving... I'll obey... just feed me please...** 🍖"

                            # Create urgent warning embed
                            warning_embed = discord.Embed(
                                title="🚨🚨🚨 **IMMINENT DEATH WARNING** 🚨🚨🚨",
                                description=begging_message,
                                color=0xFF0000
                            )
                            warning_embed.add_field(
                                name=f"💀 **{name} IS ABOUT TO DIE** 💀",
                                value=f"Health: {health_display}\nStomach: {hunger_display}",
                                inline=False
                            )

                            commands_needed = []
                            if health <= HEALTH_CRITICAL_WARNING:
                                commands_needed.append("`!heal` for health")
                            if hunger >= HUNGER_CRITICAL_WARNING:
                                commands_needed.append("`!feed` for hunger")

                            warning_embed.add_field(
                                name=action_message,
                                value=f"Use {' and '.join(commands_needed)} **IMMEDIATELY**\nNext decay cycle = **DEATH**",
                                inline=False
                            )
                            warning_embed.set_footer(text="⏰ You have less than 2 minutes to save your Seth!")

                            await warning_channel.send(embed=warning_embed)

            # Announce deaths in #seth-graveyard specifically
            if deaths and self.bot.guilds:
                for guild in self.bot.guilds:
                    graveyard_channel = discord.utils.get(guild.text_channels, name='seth-graveyard')

                    if graveyard_channel:
                        for death in deaths:
                            user = self.bot.get_user(death[3])
                            embed = discord.Embed(
                                title="💀 **SETH HAS DIED!**",
                                description=f"**{death[0]}** (Generation {death[1]}) has passed away",
                                color=0x000000
                            )
                            embed.add_field(name="Cause of Death", value=death[2], inline=False)
                            if user:
                                embed.add_field(name="Owner", value=user.mention, inline=False)
                            embed.set_footer(text="Press F to pay respects")

                            msg = await graveyard_channel.send(embed=embed)
                            await msg.add_reaction('🇫')

                    home_channel = discord.utils.get(guild.text_channels, name='seth-home')
                    if not home_channel:
                        home_channel = discord.utils.get(guild.text_channels, name='general')

                    if home_channel and home_channel != graveyard_channel:
                        for death in deaths:
                            brief_embed = discord.Embed(
                                title="💀 SETH HAS DIED!",
                                description=f"**{death[0]}** (Gen {death[1]}) has died!",
                                color=discord.Color.dark_red()
                            )
                            brief_embed.add_field(name="Cause", value=death[2], inline=True)
                            brief_embed.set_footer(text="Use !start [name] to continue the bloodline")
                            await home_channel.send(embed=brief_embed)

    @decay_task.before_loop
    async def before_decay(self) -> None:
        await self.bot.wait_until_ready()
        print("⏰ Decay system started! Seths will now age every 2 minutes...")

    @commands.command(name='decay')
    @commands.is_owner()
    async def force_decay(self, ctx: commands.Context) -> None:
        """Force a decay cycle (owner only)"""
        await self.decay_task()
        await ctx.send("⏰ Forced decay cycle complete!")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Decay(bot))
