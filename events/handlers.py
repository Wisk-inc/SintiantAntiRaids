import discord
from discord.ext import commands
import time
from collections import deque
from ai.brain import ask_ai
from modules.snapshot.capture import save_snapshot
from modules.snapshot.rebuild import rebuild_channels
from core.logger import logger

class SentinelEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Rolling windows for raid detection
        self.channel_deletes = {} # guild_id -> deque of timestamps
        self.channel_creates = {} # guild_id -> deque of timestamps
        self.role_deletes = {} # guild_id -> deque of timestamps
        self.role_creates = {} # guild_id -> deque of timestamps
        self.bans = {} # guild_id -> deque of timestamps
        self.everyone_pings = {} # guild_id -> user_id -> deque of timestamps

        # Detection Thresholds
        self.RAID_THRESHOLD_SEC = 10
        self.DELETE_LIMIT = 3
        self.CREATE_LIMIT = 5
        self.BAN_LIMIT = 3

    # --- HELPER: Rolling Window Check ---
    def check_threshold(self, guild_id, storage, limit):
        now = time.time()
        if guild_id not in storage:
            storage[guild_id] = deque()
        storage[guild_id].append(now)
        while storage[guild_id] and now - storage[guild_id][0] > self.RAID_THRESHOLD_SEC:
            storage[guild_id].popleft()
        return len(storage[guild_id]) >= limit

    # --- BOT READY & JOIN EVENTS ---
    @commands.Cog.listener()
    async def on_ready(self):
        # Snapshot every guild on bot ready
        for guild in self.bot.guilds:
            save_snapshot(guild)
        print("✅ Snapshot of all guilds completed on bot ready.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print(f"👋 Joined new guild: {guild.name} ({guild.id})")
        save_snapshot(guild)
        # Introduction message
        owner = guild.owner
        if owner:
            embed = discord.Embed(
                title="⚔️ SENTINEL HAS ARRIVED",
                description=f"I have successfully snapshot **{guild.name}** and guards are now active.",
                color=discord.Color.green()
            )
            try: await owner.send(embed=embed)
            except: pass

    # --- CHANNEL EVENTS ---
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        print(f"🗑️ Channel deleted: {channel.name} in {guild.name}")
        if self.check_threshold(guild.id, self.channel_deletes, self.DELETE_LIMIT):
            print(f"🚨 RAID DETECTED: Mass Channel Deletion in {guild.name}!")
            # Immediate AI Action
            event_context = f"Mass channel deletion detected in guild {guild.name} ({guild.id}). {len(self.channel_deletes[guild.id])} channels deleted in {self.RAID_THRESHOLD_SEC}s."
            ai_verdict = await ask_ai(event_context)
            if ai_verdict and ai_verdict.get("verdict") == "RAID_DETECTED":
                await rebuild_channels(guild, scope="channels")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        print(f"➕ Channel created: {channel.name} in {guild.name}")
        if self.check_threshold(guild.id, self.channel_creates, self.CREATE_LIMIT):
            print(f"🚨 RAID DETECTED: Mass Channel Creation in {guild.name}!")
            # AI logic would follow here for spam prevention

    # --- ROLE EVENTS ---
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        print(f"🗑️ Role deleted: {role.name} in {guild.name}")
        if self.check_threshold(guild.id, self.role_deletes, self.DELETE_LIMIT):
            print(f"🚨 RAID DETECTED: Mass Role Deletion in {guild.name}!")
            # Action: Rebuild roles or AI consult

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = role.guild
        print(f"➕ Role created: {role.name} in {guild.name}")
        if self.check_threshold(guild.id, self.role_creates, self.CREATE_LIMIT):
            print(f"🚨 RAID DETECTED: Mass Role Creation in {guild.name}!")

    # --- MEMBER EVENTS ---
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        print(f"🔨 User banned: {user.name} in {guild.name}")
        if self.check_threshold(guild.id, self.bans, self.BAN_LIMIT):
            print(f"🚨 RAID DETECTED: Mass Ban in {guild.name}!")
            # Find the executor in audit logs and potentially ban them

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"👤 Member joined: {member.name} to {member.guild.name}")
        # AI Profile Check logic could go here

    # --- MESSAGE EVENTS ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return

        # @everyone ping spam detection
        if message.mention_everyone:
            guild_id = message.guild.id
            user_id = message.author.id
            now = time.time()
            if guild_id not in self.everyone_pings: self.everyone_pings[guild_id] = {}
            if user_id not in self.everyone_pings[guild_id]: self.everyone_pings[guild_id][user_id] = deque()

            self.everyone_pings[guild_id][user_id].append(now)
            while self.everyone_pings[guild_id][user_id] and now - self.everyone_pings[guild_id][user_id][0] > 60:
                self.everyone_pings[guild_id][user_id].popleft()

            if len(self.everyone_pings[guild_id][user_id]) >= 2:
                print(f"🚨 ALERT: @everyone spam from {message.author.name} in {message.guild.name}!")
                # Immediate Action: Kick or Ban via AI
                event_context = f"@everyone spam from {message.author.name} (ID: {user_id}) in {message.guild.name}."
                ai_verdict = await ask_ai(event_context)
                if ai_verdict and ai_verdict.get("verdict") in ["RAID_DETECTED", "SUSPICIOUS"]:
                    try: await message.author.ban(reason="SENTINEL: @everyone spam detection")
                    except: pass

async def setup(bot: commands.Bot):
    await bot.add_cog(SentinelEvents(bot))
