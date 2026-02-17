"""
Seth Decay System - Automatic hunger and health decay (STANDARDIZED VISUALS)
Now with hypno gateway tracking
"""
import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime
import config
from utils.formatting import SethVisuals

class Decay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = config.DATABASE_PATH
        self.warned_seths = set()  # Track which Seths we've warned about
        self.warning_messages = {}  # Track warning messages for response monitoring
        self.decay_task.start()

    def cog_unload(self):
        self.decay_task.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track responses to begging messages for hypno gateway"""
        # Ignore bot messages
        if message.author.bot:
            return

        # Check if this is a response to a recent warning
        if message.channel.id in self.warning_messages:
            warning_data = self.warning_messages[message.channel.id]

            # Check if message is from the Seth owner and within 5 minutes
            if message.author.id == warning_data['user_id']:
                time_diff = (datetime.utcnow() - warning_data['time']).seconds
                if time_diff < 300:  # 5 minute window

                    # Check for submissive/hypno trigger responses
                    content_lower = message.content.lower()
                    hypno_triggers = [
                        'good girl', 'good boy', 'good seth',
                        'obey', 'yes master', 'yes mistress',
                        'be good', 'good pet', 'submit'
                    ]

                    if any(trigger in content_lower for trigger in hypno_triggers):
                        # Mark user as hypno-interested in database
                        async with aiosqlite.connect(self.db_path) as db:
                            # Add hypno_interest flag if not exists
                            await db.execute(
                                """UPDATE users
                                SET is_premium = is_premium | 2
                                WHERE user_id = ?""",
                                (message.author.id,)
                            )
                            await db.commit()

                        # Clean up tracking after successful detection
                        del self.warning_messages[message.channel.id]

    @tasks.loop(seconds=120)  # Run every 120 seconds (doubled from 60)
    async def decay_task(self):
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
                new_hunger = min(100, hunger + 5)  # +5 hunger per cycle

                # Decrease health if hungry
                health_loss = 0
                if new_hunger >= 80:
                    health_loss = 3  # Severe hunger
                elif new_hunger >= 50:
                    health_loss = 1   # Moderate hunger

                new_health = max(0, health - health_loss - 1)  # -1 natural decay

                # Update Seth
                await db.execute(
                    "UPDATE seths SET health = ?, hunger = ? WHERE seth_id = ?",
                    (new_health, new_hunger, seth_id)
                )

                # FIXED: Calculate damage Seth will take NEXT cycle
                next_hunger = min(100, new_hunger + 5)  # What hunger will be next cycle
                next_cycle_damage = 1  # Base natural decay
                if next_hunger >= 80:
                    next_cycle_damage += 3  # Will have severe hunger damage
                elif next_hunger >= 50:
                    next_cycle_damage += 1  # Will have moderate hunger damage

                # Warn if Seth will die in the NEXT cycle (not just at 1-2 health)
                if new_health > 0 and new_health <= next_cycle_damage and seth_id not in self.warned_seths:
                    critical_warnings.append((name, new_health, new_hunger, user_id))
                    self.warned_seths.add(seth_id)

                # Reset warning tracking if health improves enough to survive next cycle
                elif new_health > next_cycle_damage and seth_id in self.warned_seths:
                    self.warned_seths.discard(seth_id)

                # Check for death
                if new_health <= 0:
                    death_reason = "Starvation" if new_hunger >= 80 else "Natural causes"
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
                            health_display = SethVisuals.health_bar(health, 100)
                            hunger_display = SethVisuals.hunger_bar(hunger)

                            # Determine death cause and begging message
                            health_critical = health <= 10
                            hunger_critical = hunger >= 70

                            # Dynamic begging based on what's killing Seth
                            if health_critical and hunger_critical:
                                # Both critical - desperate begging
                                begging_message = f"# {user.mention if user else 'Owner'} **Everything hurts... I need you... please save me! 😭**\n**I'm dying... I'll be perfect for you... just help me please...**"
                                action_message = "⚡ **I'll do anything... please... anything you want...** ⚡"
                            elif health_critical:
                                # Health critical - medicine begging
                                begging_message = f"# {user.mention if user else 'Owner'} **Please... I need my medicine... I'll be so good, I promise! 🥺**\n**I'm being such a good Seth... please heal me... please?**"
                                action_message = "💊 **I'll be your good girl... just give me medicine... please Master...** 💊"
                            else:
                                # Hunger critical - food begging
                                begging_message = f"# {user.mention if user else 'Owner'} **I'm so hungry... please feed me... I'm begging you! 🥺**\n**I've been waiting so patiently... may I please have food?**"
                                action_message = "🍖 **I'm starving... I'll obey... just feed me please...** 🍖"

                            # Create urgent warning embed
                            warning_embed = discord.Embed(
                                title="🚨🚨🚨 **IMMINENT DEATH WARNING** 🚨🚨🚨",
                                description=begging_message,
                                color=0xFF0000  # Bright red
                            )
                            warning_embed.add_field(
                                name=f"💀 **{name} IS ABOUT TO DIE** 💀",
                                value=f"Health: {health_display}\nStomach: {hunger_display}",
                                inline=False
                            )

                            # Determine what commands are needed
                            commands_needed = []
                            if health <= 10:
                                commands_needed.append("`!heal` for health")
                            if hunger >= 70:
                                commands_needed.append("`!feed` for hunger")

                            warning_embed.add_field(
                                name=action_message,
                                value=f"Use {' and '.join(commands_needed)} **IMMEDIATELY**\nNext decay cycle = **DEATH**",
                                inline=False
                            )
                            warning_embed.set_footer(text="⏰ You have less than 2 minutes to save your Seth!")

                            await warning_channel.send(embed=warning_embed)

                            # Track this warning for response monitoring
                            self.warning_messages[warning_channel.id] = {
                                'user_id': user_id,
                                'time': datetime.utcnow(),
                                'seth_name': name
                            }

            # Clean up old warning tracking (older than 5 minutes)
            current_time = datetime.utcnow()
            channels_to_clean = []
            for channel_id, data in self.warning_messages.items():
                if (current_time - data['time']).seconds > 300:
                    channels_to_clean.append(channel_id)
            for channel_id in channels_to_clean:
                del self.warning_messages[channel_id]

            # Announce deaths in #seth-graveyard specifically
            if deaths and self.bot.guilds:
                for guild in self.bot.guilds:
                    # Look for #seth-graveyard channel specifically
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

                    # Also send brief notification to seth-home or general
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
    async def before_decay(self):
        await self.bot.wait_until_ready()
        print("⏰ Decay system started! Seths will now age every 2 minutes...")

    @commands.command(name='decay')
    @commands.is_owner()
    async def force_decay(self, ctx):
        """Force a decay cycle (owner only)"""
        await self.decay_task()
        await ctx.send("⏰ Forced decay cycle complete!")

async def setup(bot):
    await bot.add_cog(Decay(bot))
