import discord
import time
from collections import deque
from core.config import RAID_THRESHOLD_SEC, BAN_LIMIT
from ai.brain import ask_ai
from core.logger import logger

class MemberGuard:
    def __init__(self, bot):
        self.bot = bot
        self.bans = {} # guild_id -> deque of timestamps
        self.kicks = {} # guild_id -> deque of timestamps

    async def on_member_ban(self, guild, user):
        now = time.time()
        if guild.id not in self.bans:
            self.bans[guild.id] = deque()
        self.bans[guild.id].append(now)

        while self.bans[guild.id] and now - self.bans[guild.id][0] > RAID_THRESHOLD_SEC:
            self.bans[guild.id].popleft()

        if len(self.bans[guild.id]) >= BAN_LIMIT:
            logger.warning(f"Mass ban detected in guild {guild.id}!")
            # Audit log to find executor
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                executor = entry.user
                # AI consult
                event_context = f"Mass ban detected in guild {guild.name}. {len(self.bans[guild.id])} bans in {RAID_THRESHOLD_SEC}s. Executor: {executor.name} (ID: {executor.id})"
                ai_verdict = await ask_ai(event_context)
                # Logic to unban victims and ban executor if AI says so
                break

    async def on_member_remove(self, member):
        # Could be kick or leave. Check audit logs for kick.
        pass
