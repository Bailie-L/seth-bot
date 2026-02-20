"""
Seth Trading System - Exchange resources between users (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands
import aiosqlite
import config
import asyncio
from utils.formatting import SethVisuals

class Trading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = config.DATABASE_PATH
        self.pending_trades = {}  # Store pending trade offers

    @commands.command(name='trade')
    async def trade(self, ctx, *, args=None):
        """Trade resources with another user"""
        if not args:
            embed = discord.Embed(
                title="📦 **Trading Guide**",
                description="Trade resources with other Seth owners!",
                color=0x3498db
            )
            embed.add_field(
                name="Usage",
                value="`!trade @user [food/medicine/coal] [amount]`",
                inline=False
            )
            embed.add_field(
                name="Example",
                value="`!trade @friend food 3`\n`!trade @buddy coal 10`",
                inline=False
            )
            embed.add_field(
                name="Your Resources",
                value="Use `!inventory` to check what you have",
                inline=False
            )
            await ctx.send(embed=embed)
            return

        # Parse arguments
        parts = args.split()
        if len(parts) < 3:
            await ctx.send("❌ Usage: `!trade @user [food/medicine/coal] [amount]`")
            return

        # Get member from mentions or by name
        member = None
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
            resource_index = 1
        else:
            # Try to find member by name
            potential_name = parts[0].replace('@', '')
            member = discord.utils.get(ctx.guild.members, name=potential_name)
            if not member:
                member = discord.utils.get(ctx.guild.members, display_name=potential_name)
            resource_index = 1

        if not member:
            await ctx.send("❌ User not found! Make sure to @ mention them properly")
            return

        # Get resource and amount
        try:
            resource = parts[resource_index].lower()
            amount = int(parts[resource_index + 1])
        except (IndexError, ValueError):
            await ctx.send("❌ Usage: `!trade @user [food/medicine/coal] [amount]`")
            return

        # Validation checks
        if member.id == ctx.author.id:
            await ctx.send("🤔 You can't trade with yourself!")
            return

        if member.bot:
            await ctx.send("🤖 Bots don't have Seths! They can't trade.")
            return

        # Validate resource type
        if resource not in ['food', 'medicine', 'coal']:
            await ctx.send("❌ Invalid resource! Choose: `food`, `medicine`, or `coal`")
            return

        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return

        if amount > 100:
            await ctx.send("❌ That's too much! Trade max 100 at a time.")
            return

        # Check if users have Seths and resources
        async with aiosqlite.connect(self.db_path) as db:
            # Check author has Seth
            cursor = await db.execute(
                "SELECT name FROM seths WHERE user_id = ? AND is_alive = 1",
                (ctx.author.id,)
            )
            author_seth = await cursor.fetchone()
            if not author_seth:
                await ctx.send("💀 You need a living Seth to trade!")
                return

            # Check target has Seth
            cursor = await db.execute(
                "SELECT name FROM seths WHERE user_id = ? AND is_alive = 1",
                (member.id,)
            )
            target_seth = await cursor.fetchone()
            if not target_seth:
                await ctx.send(f"💀 {member.name} doesn't have a living Seth!")
                return

            # Check author has enough resources
            cursor = await db.execute(
                f"SELECT {resource} FROM resources WHERE user_id = ?",
                (ctx.author.id,)
            )
            result = await cursor.fetchone()
            if not result:
                await ctx.send("❌ You have no resources! Use `!mine` to gather some.")
                return

            current_amount = result[0]
            if current_amount < amount:
                # Use visual bar to show shortage
                resource_display = SethVisuals.resource_bar(current_amount, amount, show_fraction=True)
                embed = discord.Embed(
                    title="❌ Insufficient Resources",
                    description=f"Not enough {resource}!",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name=f"{resource.capitalize()} Status",
                    value=f"{resource_display}\nYou have: **{current_amount}** | Need: **{amount}**",
                    inline=False
                )
                await ctx.send(embed=embed)
                return

        # Create trade offer
        trade_id = f"{ctx.author.id}:{member.id}:{ctx.message.id}"
        self.pending_trades[trade_id] = {
            'from': ctx.author,
            'to': member,
            'resource': resource,
            'amount': amount,
            'channel': ctx.channel
        }

        # Resource emoji mapping
        resource_emojis = {
            'food': '🍖',
            'medicine': '💊',
            'coal': '⚫'
        }

        # Send trade offer with standardized display
        embed = discord.Embed(
            title="🤝 **Trade Offer**",
            description=f"{ctx.author.mention} wants to trade with {member.mention}!",
            color=0xf39c12
        )
        embed.add_field(
            name="From",
            value=f"{ctx.author.name}'s **{author_seth[0]}**",
            inline=True
        )
        embed.add_field(
            name="Offering",
            value=f"{resource_emojis.get(resource, '')} **{amount}** {resource.capitalize()}",
            inline=True
        )
        embed.add_field(
            name="To",
            value=f"{member.name}'s **{target_seth[0]}**",
            inline=True
        )
        embed.set_footer(text=f"{member.name}, react ✅ to accept or ❌ to decline (30s)")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        # Wait for response
        def check(reaction, user):
            return (user.id == member.id and
                   reaction.message.id == msg.id and
                   str(reaction.emoji) in ['✅', '❌'])

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == '✅':
                # Execute trade
                async with aiosqlite.connect(self.db_path) as db:
                    # Remove from sender
                    await db.execute(
                        f"UPDATE resources SET {resource} = {resource} - ? WHERE user_id = ?",
                        (amount, ctx.author.id)
                    )
                    # Add to receiver
                    await db.execute(
                        f"UPDATE resources SET {resource} = {resource} + ? WHERE user_id = ?",
                        (amount, member.id)
                    )
                    await db.commit()

                embed = discord.Embed(
                    title="✅ **Trade Complete!**",
                    description="Resources successfully transferred!",
                    color=0x2ecc71
                )
                embed.add_field(
                    name="Transaction",
                    value=f"{ctx.author.mention} ➡️ **{amount}** {resource_emojis.get(resource, '')} {resource} ➡️ {member.mention}",
                    inline=False
                )
                embed.add_field(
                    name="Seth Involved",
                    value=f"**{author_seth[0]}** traded with **{target_seth[0]}**",
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ **Trade Declined!** {member.name} rejected the offer.")

        except asyncio.TimeoutError:
            await ctx.send("⏰ **Trade Expired!** The offer timed out after 30 seconds.")
        finally:
            # Clean up pending trade
            if trade_id in self.pending_trades:
                del self.pending_trades[trade_id]

async def setup(bot):
    await bot.add_cog(Trading(bot))
