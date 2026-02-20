"""
Seth Public Features - Server-wide visibility
"""
import discord
from discord.ext import commands
import aiosqlite
import config
from datetime import datetime

class Public(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = config.DATABASE_PATH

    @commands.command(name='server')
    async def server_seths(self, ctx):
        """Show all living Seths in the server"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT s.name, s.generation, s.health, s.hunger, s.birth_time, u.discord_name
                FROM seths s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.is_alive = 1
                ORDER BY s.generation DESC, s.health DESC"""
            )
            living_seths = await cursor.fetchall()

            if not living_seths:
                await ctx.send("💀 No living Seths in this server!")
                return

            embed = discord.Embed(
                title="🌍 **Living Seths in Server**",
                description=f"Population: {len(living_seths)} Seths",
                color=0x2ecc71
            )

            for name, gen, health, hunger, birth_time, owner in living_seths:
                # Calculate age
                birth = datetime.fromisoformat(birth_time)
                age_minutes = int((datetime.now() - birth).total_seconds() / 60)

                # Health status emoji
                if health > 75:
                    status = "💚"
                elif health > 25:
                    status = "💛"
                else:
                    status = "💔"

                # Hunger status
                if hunger > 80:
                    hunger_status = "🔴 Starving!"
                elif hunger > 50:
                    hunger_status = "🟡 Hungry"
                else:
                    hunger_status = "🟢 Fed"

                embed.add_field(
                    name=f"{status} {name} (Gen {gen})",
                    value=f"Owner: {owner}\n❤️ {health}/100 | {hunger_status}\n⏰ Age: {age_minutes} min",
                    inline=True
                )

            embed.set_footer(text="Use !compare @user to compare Seths")
            await ctx.send(embed=embed)

    @commands.command(name='compare')
    async def compare_seths(self, ctx, *, target=None):
        """Compare your Seth with another user's Seth"""
        if target is None:
            await ctx.send("⚠️ Usage: `!compare @user` (mention someone)")
            return

        # Try to get member from mentions
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            # Try to find member by name/nickname
            try:
                # Remove @ if present
                target = target.replace('@', '')
                member = discord.utils.get(ctx.guild.members, name=target)
                if not member:
                    member = discord.utils.get(ctx.guild.members, nick=target)
                if not member:
                    await ctx.send(f"❌ User '{target}' not found! Use `!compare @user` with a mention")
                    return
            except Exception:
                await ctx.send("❌ Invalid user! Use `!compare @user` with a mention")
                return

        if member.id == ctx.author.id:
            await ctx.send("🤔 You can't compare with yourself!")
            return

        if member.bot:
            await ctx.send("🤖 Bots don't have Seths!")
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Get author's Seth
            cursor = await db.execute(
                """SELECT s.name, s.generation, s.health, s.hunger, s.birth_time
                FROM seths s
                WHERE s.user_id = ? AND s.is_alive = 1""",
                (ctx.author.id,)
            )
            author_seth = await cursor.fetchone()

            # Get target's Seth
            cursor = await db.execute(
                """SELECT s.name, s.generation, s.health, s.hunger, s.birth_time
                FROM seths s
                WHERE s.user_id = ? AND s.is_alive = 1""",
                (member.id,)
            )
            target_seth = await cursor.fetchone()

            if not author_seth:
                await ctx.send("💀 You don't have a living Seth! Use `!start [name]`")
                return

            if not target_seth:
                await ctx.send(f"💀 {member.name} doesn't have a living Seth!")
                return

            # Parse data
            a_name, a_gen, a_health, a_hunger, a_birth = author_seth
            t_name, t_gen, t_health, t_hunger, t_birth = target_seth

            # Calculate ages
            a_age = int((datetime.now() - datetime.fromisoformat(a_birth)).total_seconds() / 60)
            t_age = int((datetime.now() - datetime.fromisoformat(t_birth)).total_seconds() / 60)

            # Determine winner
            a_score = a_health + (100 - a_hunger) + (a_gen * 10) + (a_age // 10)
            t_score = t_health + (100 - t_hunger) + (t_gen * 10) + (t_age // 10)

            if a_score > t_score:
                winner = f"🏆 {ctx.author.name}'s {a_name} is superior!"
                color = 0x2ecc71
            elif t_score > a_score:
                winner = f"🏆 {member.name}'s {t_name} is superior!"
                color = 0xe74c3c
            else:
                winner = "🤝 It's a tie!"
                color = 0xf39c12

            embed = discord.Embed(
                title="⚔️ **Seth Comparison**",
                description=winner,
                color=color
            )

            # Author's Seth
            embed.add_field(
                name=f"{ctx.author.name}'s {a_name}",
                value=f"**Gen:** {a_gen}\n**Health:** {a_health}/100\n**Hunger:** {a_hunger}/100\n**Age:** {a_age} min\n**Score:** {a_score}",
                inline=True
            )

            # VS
            embed.add_field(
                name="⚔️",
                value="**VS**",
                inline=True
            )

            # Target's Seth
            embed.add_field(
                name=f"{member.name}'s {t_name}",
                value=f"**Gen:** {t_gen}\n**Health:** {t_health}/100\n**Hunger:** {t_hunger}/100\n**Age:** {t_age} min\n**Score:** {t_score}",
                inline=True
            )

            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Public(bot))
