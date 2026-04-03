import discord
from discord.ext import commands
from core.bot import SentinelBot
from modules.guard.channel_guard import ChannelGuard
from modules.guard.message_guard import MessageGuard
from modules.guard.role_guard import RoleGuard
from modules.guard.webhook_guard import WebhookGuard
from modules.guard.emoji_guard import EmojiGuard
from modules.guard.member_guard import MemberGuard
from modules.snapshot.capture import capture_guild_snapshot
from core.logger import logger

class SentinelEvents(commands.Cog):
    def __init__(self, bot: SentinelBot):
        self.bot = bot
        self.channel_guard = ChannelGuard(bot)
        self.message_cache_guard = MessageGuard(bot)
        self.role_guard = RoleGuard(bot)
        self.webhook_guard = WebhookGuard(bot)
        self.emoji_guard = EmojiGuard(bot)
        self.member_guard = MemberGuard(bot)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.logger.info(f"Joined new guild: {guild.name} ({guild.id})")
        # Snapshot on join
        capture_guild_snapshot(guild)
        # Welcome message
        owner = guild.owner
        if owner:
            try:
                await owner.send(f"⚔️ SENTINEL HAS ARRIVED. I have snapshot your server '{guild.name}' and guards are active.")
            except:
                pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.channel_guard.on_channel_delete(channel)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.message_cache_guard.on_message(message)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        await self.message_cache_guard.on_bulk_message_delete(messages)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.role_guard.on_role_delete(role)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.webhook_guard.on_webhook_update(channel)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        # We need to find what was deleted or created
        deleted = set(before) - set(after)
        created = set(after) - set(before)
        for emoji in deleted:
            await self.emoji_guard.on_emoji_delete(emoji)
        for emoji in created:
            await self.emoji_guard.on_emoji_create(emoji)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.member_guard.on_member_ban(guild, user)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.member_guard.on_member_remove(member)

async def setup(bot):
    await bot.add_cog(SentinelEvents(bot))
