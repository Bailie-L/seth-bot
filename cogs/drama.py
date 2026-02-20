"""
Seth Drama Engine v2.0 - Real NPC Relationships & Drama (STANDARDIZED VISUALS)
"""
import discord
from discord.ext import commands, tasks
import aiosqlite
import config
import random
from datetime import datetime
import asyncio
from utils.formatting import SethVisuals

class DramaV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = config.DATABASE_PATH

        # NPC personalities
        self.npcs = {
            'Luna': {'personality': 'romantic', 'job': 'farmer', 'temper': 30},
            'Marcus': {'personality': 'ambitious', 'job': 'builder', 'temper': 70},
            'Felix': {'personality': 'aggressive', 'job': 'guard', 'temper': 90},
            'Aria': {'personality': 'mysterious', 'job': 'trader', 'temper': 20},
            'Thorne': {'personality': 'wise', 'job': 'elder', 'temper': 10}
        }

        # Drama templates based on relationship states
        self.drama_templates = {
            'romance_start': [
                "💕 {npc1} was seen bringing flowers to {npc2} at midnight!",
                "💕 {npc1} carved '{npc2} + {npc1}' into the old oak tree!",
                "💕 {npc1} asked Thorne about marriage traditions while staring at {npc2}!"
            ],
            'romance_conflict': [
                "💔 {npc1} saw {npc2} laughing with {rival} and stormed off!",
                "😡 {npc1} threw {npc2}'s gift into the well after seeing them with {rival}!",
                "🔥 {npc1} and {rival} are fighting over {npc2} in the town square!"
            ],
            'betrayal': [
                "🗡️ {npc1} discovered {npc2} has been stealing from their shop!",
                "😱 {npc1} overheard {npc2} spreading vicious rumors about them!",
                "💰 {npc2} sabotaged {npc1}'s work to win the village contract!"
            ],
            'alliance': [
                "🤝 {npc1} and {npc2} announced a business partnership!",
                "⚔️ {npc1} defended {npc2} from {rival}'s accusations!",
                "🏘️ {npc1} and {npc2} are building something secret together!"
            ],
            'mystery': [
                "🌙 {npc1} was seen sneaking into the forbidden forest...",
                "📜 A mysterious letter about {npc1} appeared on {npc2}'s door!",
                "👁️ {npc1} knows something about {npc2} that nobody else does..."
            ],
            'scandal': [
                "🍺 {npc1} got drunk and revealed {npc2}'s biggest secret!",
                "😈 {npc1} and {npc2} were caught together by {rival}!",
                "🎭 The truth about {npc1}'s past with {npc2} just came out!"
            ]
        }

        # Current active drama event for voting
        self.active_drama = None
        self.drama_channel = None

        # Start drama loop when cog loads
        self.drama_loop.start()

    def cog_unload(self):
        self.drama_loop.cancel()

    async def get_relationship(self, npc1, npc2):
        """Get relationship score between two NPCs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT relationship_score, relationship_type
                FROM npc_relationships
                WHERE (npc1 = ? AND npc2 = ?) OR (npc1 = ? AND npc2 = ?)
            ''', (npc1, npc2, npc2, npc1))
            row = await cursor.fetchone()
            return row if row else (50, 'neutral')

    async def update_relationship(self, npc1, npc2, change, event_type=None):
        """Update relationship between NPCs"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current score
            score, _ = await self.get_relationship(npc1, npc2)
            new_score = max(0, min(100, score + change))

            # Determine relationship type based on score
            if new_score >= 80:
                rel_type = 'lovers'
            elif new_score >= 60:
                rel_type = 'friends'
            elif new_score >= 40:
                rel_type = 'neutral'
            elif new_score >= 20:
                rel_type = 'rivals'
            else:
                rel_type = 'enemies'

            # Update both directions
            await db.execute('''
                UPDATE npc_relationships
                SET relationship_score = ?, relationship_type = ?, last_event = ?
                WHERE (npc1 = ? AND npc2 = ?) OR (npc1 = ? AND npc2 = ?)
            ''', (new_score, rel_type, event_type, npc1, npc2, npc2, npc1))

            await db.commit()
            return new_score, rel_type

    async def get_npc_state(self, npc_name):
        """Get current NPC state"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT current_mood, dating, rival FROM npc_states
                WHERE npc_name = ?
            ''', (npc_name,))
            row = await cursor.fetchone()
            return row if row else ('normal', None, None)

    async def update_npc_state(self, npc_name, **kwargs):
        """Update NPC state"""
        async with aiosqlite.connect(self.db_path) as db:
            for key, value in kwargs.items():
                await db.execute(f'''
                    UPDATE npc_states
                    SET {key} = ?
                    WHERE npc_name = ?
                ''', (value, npc_name))
            await db.commit()

    async def generate_drama_event(self):
        """Generate drama based on current relationships"""
        # Get all NPCs and their relationships
        npc_list = list(self.npcs.keys())

        # Find interesting relationship dynamics

        async with aiosqlite.connect(self.db_path) as db:
            # Find lovers
            cursor = await db.execute('''
                SELECT npc1, npc2 FROM npc_relationships
                WHERE relationship_type = 'lovers'
            ''')
            lovers = await cursor.fetchall()

            # Find enemies
            cursor = await db.execute('''
                SELECT npc1, npc2 FROM npc_relationships
                WHERE relationship_type IN ('rivals', 'enemies')
            ''')
            enemies = await cursor.fetchall()

        # Generate event based on current state
        event_type = None
        if lovers and random.random() < 0.4:
            # Romance drama
            couple = random.choice(lovers)
            if enemies:
                # Love triangle
                rival = random.choice(enemies)[0]
                event_type = 'romance_conflict'
                template = random.choice(self.drama_templates[event_type])
                description = template.format(
                    npc1=couple[0],
                    npc2=couple[1],
                    rival=rival
                )
                return event_type, description, couple[0], couple[1], rival
            else:
                # Sweet romance
                event_type = 'romance_start'
                template = random.choice(self.drama_templates[event_type])
                description = template.format(npc1=couple[0], npc2=couple[1])
                return event_type, description, couple[0], couple[1], None

        elif enemies and random.random() < 0.5:
            # Conflict drama
            rivals = random.choice(enemies)
            event_type = random.choice(['betrayal', 'scandal'])
            template = random.choice(self.drama_templates[event_type])
            description = template.format(
                npc1=rivals[0],
                npc2=rivals[1],
                rival=random.choice([n for n in npc_list if n not in rivals])
            )
            return event_type, description, rivals[0], rivals[1], None

        else:
            # Random drama
            random.shuffle(npc_list)
            npc1, npc2 = npc_list[0], npc_list[1]
            event_type = random.choice(['mystery', 'alliance', 'scandal'])
            template = random.choice(self.drama_templates[event_type])

            # Format based on template needs
            if '{rival}' in template:
                description = template.format(
                    npc1=npc1,
                    npc2=npc2,
                    rival=npc_list[2]
                )
            else:
                description = template.format(npc1=npc1, npc2=npc2)

            return event_type, description, npc1, npc2, None

    @tasks.loop(minutes=5)  # Drama every 5 minutes for testing
    async def drama_loop(self):
        """Generate and post drama events"""
        if not self.drama_channel:
            for guild in self.bot.guilds:
                # First try village-drama channel
                channel = discord.utils.get(guild.channels, name='village-drama')
                if not channel:
                    # Fallback to seth-graveyard
                    channel = discord.utils.get(guild.channels, name='seth-graveyard')
                if channel:
                    self.drama_channel = channel
                    print(f"✅ Drama channel set to: #{channel.name}")
                    break

        if not self.drama_channel:
            return

        # Generate drama
        try:
            event_type, description, npc1, npc2, npc3 = await self.generate_drama_event()
        except Exception as e:
            print(f"Drama generation error: {e}")
            return

        # Create voting embed
        embed = discord.Embed(
            title="🎭 VILLAGE DRAMA UNFOLDS!",
            description=description,
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )

        # Add context about NPCs
        mood1, dating1, rival1 = await self.get_npc_state(npc1)
        embed.add_field(
            name=f"📊 {npc1} ({self.npcs[npc1]['job'].title()})",
            value=f"Mood: {mood1}\nDating: {dating1 or 'Nobody'}\nRival: {rival1 or 'None'}",
            inline=True
        )

        if npc2:
            mood2, dating2, rival2 = await self.get_npc_state(npc2)
            embed.add_field(
                name=f"📊 {npc2} ({self.npcs[npc2]['job'].title()})",
                value=f"Mood: {mood2}\nDating: {dating2 or 'Nobody'}\nRival: {rival2 or 'None'}",
                inline=True
            )

        # Add voting options based on event type
        if event_type == 'romance_conflict':
            embed.add_field(
                name="🗳️ **VOTE: How should this resolve?**",
                value=(
                    "1️⃣ They should work it out (relationship +20)\n"
                    "2️⃣ Time for a breakup (relationship -30)\n"
                    "3️⃣ Let them fight it out (random outcome)"
                ),
                inline=False
            )
            options = ['1️⃣', '2️⃣', '3️⃣']

        elif event_type in ['betrayal', 'scandal']:
            embed.add_field(
                name="🗳️ **VOTE: What happens next?**",
                value=(
                    "1️⃣ Forgive and forget (relationship +10)\n"
                    "2️⃣ Demand justice (become rivals)\n"
                    "3️⃣ Spread the drama (affects everyone)"
                ),
                inline=False
            )
            options = ['1️⃣', '2️⃣', '3️⃣']

        else:
            embed.add_field(
                name="🗳️ **VOTE: Your reaction?**",
                value=(
                    "👍 Support this\n"
                    "👎 Oppose this\n"
                    "🤷 Stay neutral"
                ),
                inline=False
            )
            options = ['👍', '👎', '🤷']

        # Post and add reactions
        message = await self.drama_channel.send(embed=embed)
        for emoji in options:
            await message.add_reaction(emoji)

        # Store active drama
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO drama_history (event_type, description, npc1, npc2)
                VALUES (?, ?, ?, ?)
            ''', (event_type, description, npc1, npc2))
            await db.commit()

            cursor = await db.execute('SELECT last_insert_rowid()')
            event_id = (await cursor.fetchone())[0]

        self.active_drama = {
            'message_id': message.id,
            'event_id': event_id,
            'event_type': event_type,
            'npc1': npc1,
            'npc2': npc2,
            'options': options
        }

        # Wait 3 minutes for votes (shorter for testing)
        await asyncio.sleep(180)
        await self.resolve_drama()

    async def resolve_drama(self):
        """Resolve drama based on votes"""
        if not self.active_drama or not self.drama_channel:
            return

        # Get the message
        try:
            message = await self.drama_channel.fetch_message(self.active_drama['message_id'])
        except Exception as e:
            print(f"Could not fetch drama message: {e}")
            return

        # Count votes
        votes = {opt: 0 for opt in self.active_drama['options']}
        for reaction in message.reactions:
            if str(reaction.emoji) in votes:
                votes[str(reaction.emoji)] = reaction.count - 1  # Subtract bot's reaction

        # Apply consequences
        npc1 = self.active_drama['npc1']
        npc2 = self.active_drama['npc2']

        # Determine outcome based on votes or random if no votes
        if sum(votes.values()) == 0:
            # No votes - random outcome but still update relationships
            outcome = "🎲 Nobody voted - fate decides!"
            winner_index = random.randint(0, len(self.active_drama['options']) - 1)
        else:
            winner = max(votes, key=votes.get)
            winner_index = self.active_drama['options'].index(winner)
            outcome = None  # Will be set based on event type

        # Process based on event type
        if self.active_drama['event_type'] == 'romance_conflict':
            if winner_index == 0:  # Work it out
                await self.update_relationship(npc1, npc2, 20, 'reconciled')
                if not outcome:
                    outcome = f"💕 {npc1} and {npc2} made up! Love wins!"
                else:
                    outcome += f"\n💕 Fate brings {npc1} and {npc2} together!"
            elif winner_index == 1:  # Breakup
                await self.update_relationship(npc1, npc2, -30, 'broke_up')
                await self.update_npc_state(npc1, dating=None)
                await self.update_npc_state(npc2, dating=None)
                if not outcome:
                    outcome = f"💔 {npc1} and {npc2} broke up! The village mourns..."
                else:
                    outcome += f"\n💔 Fate tears {npc1} and {npc2} apart!"
            else:  # Fight
                if random.random() < 0.5:
                    outcome_text = f"⚔️ {npc1} won the fight but lost {npc2}'s respect!"
                else:
                    outcome_text = f"⚔️ {npc2} stood their ground! {npc1} storms off!"
                await self.update_relationship(npc1, npc2, -20, 'fought')
                if not outcome:
                    outcome = outcome_text
                else:
                    outcome += f"\n{outcome_text}"

        elif self.active_drama['event_type'] in ['betrayal', 'scandal']:
            if winner_index == 0:  # Forgive
                await self.update_relationship(npc1, npc2, 10, 'forgiven')
                if not outcome:
                    outcome = f"🤝 Forgiveness prevails! {npc1} and {npc2} move forward."
                else:
                    outcome += "\n🤝 Fate grants forgiveness!"
            elif winner_index == 1:  # Justice
                await self.update_relationship(npc1, npc2, -40, 'rivals')
                await self.update_npc_state(npc1, rival=npc2)
                await self.update_npc_state(npc2, rival=npc1)
                if not outcome:
                    outcome = f"⚖️ Justice served! {npc1} and {npc2} are now bitter rivals!"
                else:
                    outcome += "\n⚖️ Fate demands justice! They become rivals!"
            else:  # Spread drama
                # Affect random other NPCs
                for npc in random.sample(list(self.npcs.keys()), 2):
                    if npc not in [npc1, npc2]:
                        await self.update_relationship(npc1, npc, -10, 'drama_spread')
                if not outcome:
                    outcome = "🔥 The drama spreads! The whole village is talking!"
                else:
                    outcome += "\n🔥 Fate spreads the chaos!"

        else:  # Mystery/Alliance
            if winner_index == 0:  # Support
                await self.update_relationship(npc1, npc2, 15, 'supported')
                if not outcome:
                    outcome = f"👍 The village supports this! {npc1} and {npc2} grow closer."
                else:
                    outcome += "\n👍 Fate smiles upon them!"
            elif winner_index == 1:  # Oppose
                await self.update_relationship(npc1, npc2, -15, 'opposed')
                if not outcome:
                    outcome = f"👎 The village opposes! {npc1} and {npc2} drift apart."
                else:
                    outcome += "\n👎 Fate drives them apart!"
            else:  # Neutral
                if not outcome:
                    outcome = "🤷 The village doesn't care. Life goes on..."
                else:
                    outcome += "\n🤷 Fate is indifferent..."

        # Post outcome
        embed = discord.Embed(
            title="📜 DRAMA RESOLVED!",
            description=outcome,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        # Show vote counts
        vote_str = "\n".join([f"{opt}: {count} votes" for opt, count in votes.items()])
        if sum(votes.values()) == 0:
            vote_str = "No votes cast - fate decided!"
        embed.add_field(name="Final Votes", value=vote_str, inline=False)

        # Show relationship changes with visual bar
        new_score, new_type = await self.get_relationship(npc1, npc2)
        relationship_bar = SethVisuals.resource_bar(new_score, 100)
        embed.add_field(
            name="Relationship Update",
            value=f"{npc1} ↔️ {npc2}\n{relationship_bar}\n**{new_type.title()}** ({new_score}/100)",
            inline=False
        )

        await self.drama_channel.send(embed=embed)

        # Clear active drama
        self.active_drama = None

    @commands.command(name='drama')
    @commands.has_permissions(administrator=True)
    async def force_drama(self, ctx):
        """Force a drama event (admin only)"""
        # Set drama channel if not set
        if not self.drama_channel:
            self.drama_channel = ctx.channel

        # Generate drama
        event_type, description, npc1, npc2, npc3 = await self.generate_drama_event()

        embed = discord.Embed(
            title="🎭 FORCED DRAMA EVENT!",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.set_footer(text=f"Triggered by {ctx.author.name}")
        await ctx.send(embed=embed)

        # Update relationships based on event
        if event_type in ['romance_start', 'alliance']:
            await self.update_relationship(npc1, npc2, 15, event_type)
        elif event_type in ['betrayal', 'scandal']:
            await self.update_relationship(npc1, npc2, -20, event_type)

    @commands.command(name='relationships')
    async def show_relationships(self, ctx):
        """Show all NPC relationships"""
        embed = discord.Embed(
            title="💕 Village Relationships",
            description="Current NPC relationship statuses",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT npc1, npc2, relationship_type, relationship_score
                FROM npc_relationships
                ORDER BY relationship_score DESC
            ''')
            relationships = await cursor.fetchall()

        # Group by relationship type
        lovers = []
        friends = []
        neutral = []
        rivals = []
        enemies = []

        for npc1, npc2, rel_type, score in relationships:
            # Use visual bar for relationship score
            rel_bar = SethVisuals.resource_bar(score, 100)
            rel_str = f"{npc1} ↔️ {npc2}\n{rel_bar}"

            if rel_type == 'lovers':
                lovers.append(f"💕 {rel_str}")
            elif rel_type == 'friends':
                friends.append(f"🤝 {rel_str}")
            elif rel_type == 'neutral':
                neutral.append(f"😐 {rel_str}")
            elif rel_type == 'rivals':
                rivals.append(f"⚔️ {rel_str}")
            elif rel_type == 'enemies':
                enemies.append(f"😠 {rel_str}")

        # Display all relationship types that exist (limit display for readability)
        if lovers:
            embed.add_field(name="Lovers", value="\n".join(lovers[:3]), inline=False)
        if friends:
            embed.add_field(name="Friends", value="\n".join(friends[:3]), inline=False)
        if neutral:
            # Show fewer neutral relationships as they're less interesting
            embed.add_field(name="Neutral", value="\n".join(neutral[:2]), inline=False)
        if rivals:
            embed.add_field(name="Rivals", value="\n".join(rivals[:3]), inline=False)
        if enemies:
            embed.add_field(name="Enemies", value="\n".join(enemies[:3]), inline=False)

        # If somehow no relationships exist at all
        if not relationships:
            embed.add_field(
                name="⚠️ No Relationships Found",
                value="The NPCs don't know each other yet! Run `!drama` to start the story.",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='npc')
    async def npc_info(self, ctx, *, npc_name: str = None):
        """Get info about a specific NPC"""
        if not npc_name:
            npc_list = ", ".join(self.npcs.keys())
            await ctx.send(f"Available NPCs: {npc_list}")
            return

        # Capitalize first letter
        npc_name = npc_name.capitalize()

        if npc_name not in self.npcs:
            await ctx.send(f"Unknown NPC! Choose from: {', '.join(self.npcs.keys())}")
            return

        # Get NPC info
        npc_data = self.npcs[npc_name]
        mood, dating, rival = await self.get_npc_state(npc_name)

        embed = discord.Embed(
            title=f"🎭 {npc_name} the {npc_data['job'].title()}",
            description=f"Personality: {npc_data['personality'].title()}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="Current Mood", value=mood.title(), inline=True)
        embed.add_field(name="Dating", value=dating or "Nobody", inline=True)
        embed.add_field(name="Rival", value=rival or "None", inline=True)

        # Use visual bar for temper
        temper_bar = SethVisuals.resource_bar(npc_data['temper'], 100)
        embed.add_field(name="Temper", value=temper_bar, inline=False)

        # Get relationships
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT npc1, npc2, relationship_type, relationship_score
                FROM npc_relationships
                WHERE npc1 = ? OR npc2 = ?
                ORDER BY relationship_score DESC
            ''', (npc_name, npc_name))
            relationships = await cursor.fetchall()

        if relationships:
            rel_strs = []
            for npc1, npc2, rel_type, score in relationships[:5]:
                other = npc2 if npc1 == npc_name else npc1
                emoji = {'lovers': '💕', 'friends': '🤝', 'neutral': '😐',
                        'rivals': '⚔️', 'enemies': '😠'}.get(rel_type, '❓')
                # Use visual bar for individual relationships
                rel_bar = SethVisuals.resource_bar(score, 100)
                rel_strs.append(f"{emoji} **{other}** - {rel_type.title()}\n{rel_bar}")

            embed.add_field(
                name="Relationships",
                value="\n".join(rel_strs),
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DramaV2(bot))
