import discord
import time
from collections import deque
from core.config import RAID_THRESHOLD_SEC, ROLE_DELETE_LIMIT
from ai.brain import ask_ai
from modules.snapshot.rebuild import rebuild_from_snapshot
from core.logger import logger

class RoleGuard:
    def __init__(self, bot):
        self.bot = bot
        self.role_deletes = {} # guild_id -> deque of timestamps

    async def on_role_delete(self, role):
        guild = role.guild
        now = time.time()

        if guild.id not in self.role_deletes:
            self.role_deletes[guild.id] = deque()

        self.role_deletes[guild.id].append(now)

        while self.role_deletes[guild.id] and now - self.role_deletes[guild.id][0] > RAID_THRESHOLD_SEC:
            self.role_deletes[guild.id].popleft()

        if len(self.role_deletes[guild.id]) >= ROLE_DELETE_LIMIT:
            logger.warning(f"Mass role deletion detected in guild {guild.id}!")
            event_context = f"Mass role deletion detected in guild {guild.name} ({guild.id}). {len(self.role_deletes[guild.id])} roles deleted in {RAID_THRESHOLD_SEC}s."
            ai_verdict = await ask_ai(event_context)
            if ai_verdict and ai_verdict.get("verdict") == "RAID_DETECTED":
                for action in ai_verdict.get("actions", []):
                    if action.type == "RESTORE" and action.params.get("scope") == "roles":
                        await rebuild_from_snapshot(guild, scope="roles")

    async def on_role_create(self, role):
        # Implement duplicate prevention and spam role detection
        pass
