"""
Seth Help System - Command documentation
"""
import discord
from discord.ext import commands
import config

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx: commands.Context, command: str | None = None) -> None:
        """Show all commands or details about a specific command"""

        if not command:
            # Show all commands
            embed = discord.Embed(
                title="🎮 **Seth Bot Commands**",
                description="Keep your Seth alive as long as possible!",
                color=0x3498db
            )

            embed.add_field(
                name="⭐ Core Commands",
                value="`!start [name]` - Create your Seth\n"
                      "`!status` - Check Seth's health/hunger\n"
                      "`!kill` - Kill your Seth instantly",
                inline=False
            )

            embed.add_field(
                name="⛏️ Economy",
                value="`!mine` - Gather resources (cooldown)\n"
                      "`!inventory` - View your resources\n"
                      "`!trade @user [type] [amount]` - Trade resources",
                inline=False
            )

            embed.add_field(
                name="💊 Maintenance",
                value="`!feed` - Use food to reduce hunger\n"
                      "`!heal` - Use medicine to restore health\n"
                      "`!damage` - Test damage (reduces health)",
                inline=False
            )

            embed.add_field(
                name="🌍 Social",
                value="`!server` - View all living Seths\n"
                      "`!compare @user` - Compare Seths\n"
                      "`!top` - Longest living Seths leaderboard",
                inline=False
            )

            embed.add_field(
                name="⚙️ System",
                value="`!ping` - Check bot latency\n"
                      "`!test` - Test database connection\n"
                      "`!drama` - Trigger event (Admin only)",
                inline=False
            )

            embed.add_field(
                name="💡 Tips",
                value="• Seths die permanently at 0 health\n"
                      "• Hunger increases over time\n"
                      "• High hunger causes faster health loss\n"
                      "• Premium role = 30s mine cooldown",
                inline=False
            )

            embed.set_footer(text=f"Use {config.BOT_PREFIX}help [command] for details")
        else:
            # Command details
            cmd_details = {
                'start': {
                    'usage': '!start [name]',
                    'desc': 'Creates your Seth or continues bloodline after death',
                    'example': '!start Bonkers',
                    'note': 'Name gets "Seth" added automatically'
                },
                'status': {
                    'usage': '!status',
                    'desc': 'Shows health, hunger, generation, and age',
                    'example': '!status',
                    'note': 'Visual bars show Seth condition'
                },
                'mine': {
                    'usage': '!mine',
                    'desc': 'Gather 0-2 food, 0-1 medicine, 1-5 coal',
                    'example': '!mine',
                    'note': 'Premium: 30s cooldown | Normal: 60s'
                },
                'trade': {
                    'usage': '!trade @user [food/medicine/coal] [amount]',
                    'desc': 'Trade resources with another player',
                    'example': '!trade @friend food 3',
                    'note': 'Target must accept within 30 seconds'
                }
            }

            if command.lower() in cmd_details:
                details = cmd_details[command.lower()]
                embed = discord.Embed(
                    title=f"📖 Command: {command}",
                    color=0x2ecc71
                )
                embed.add_field(name="Usage", value=f"`{details['usage']}`", inline=False)
                embed.add_field(name="Description", value=details['desc'], inline=False)
                embed.add_field(name="Example", value=f"`{details['example']}`", inline=False)
                if details['note']:
                    embed.add_field(name="Note", value=details['note'], inline=False)
            else:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No help available for '{command}'",
                    color=0xe74c3c
                )

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
