import time
from collections import deque
from ai.brain import ask_ai
from core.config import RAID_THRESHOLD_SEC, CHANNEL_DELETE_LIMIT
from modules.snapshot.rebuild import rebuild_from_snapshot
from core.logger import logger

class ChannelGuard:
    def __init__(self, bot):
        self.bot = bot
        self.channel_deletes = {} # guild_id -> deque of timestamps
        self.channel_creates = {} # guild_id -> deque of timestamps

    async def on_channel_delete(self, channel):
        guild = channel.guild
        now = time.time()

        if guild.id not in self.channel_deletes:
            self.channel_deletes[guild.id] = deque()

        self.channel_deletes[guild.id].append(now)

        # Clean up old timestamps
        while self.channel_deletes[guild.id] and now - self.channel_deletes[guild.id][0] > RAID_THRESHOLD_SEC:
            self.channel_deletes[guild.id].popleft()

        if len(self.channel_deletes[guild.id]) >= CHANNEL_DELETE_LIMIT:
            # Mass channel deletion detected!
            logger.warning(f"Mass channel deletion detected in guild {guild.id}!")

            # Call AI
            event_context = f"Mass channel deletion detected in guild {guild.name} ({guild.id}). {len(self.channel_deletes[guild.id])} channels deleted in {RAID_THRESHOLD_SEC}s."
            ai_verdict = await ask_ai(event_context)

            if ai_verdict and ai_verdict.get("verdict") == "RAID_DETECTED":
                # Execute actions
                for action in ai_verdict.get("actions", []):
                    if action.type == "REBUILD" and action.params.get("scope") == "channels":
                        await rebuild_from_snapshot(guild, scope="channels")
                        # Add logic to notify owner, ban responsible bot if possible
                        # Fetching audit logs to find responsible person is essential here

    async def on_channel_create(self, channel):
        # Similar logic for mass channel creation
        pass
