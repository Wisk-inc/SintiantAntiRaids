import discord
import time
from collections import deque
from core.config import RAID_THRESHOLD_SEC
from ai.brain import ask_ai
from core.logger import logger

class EmojiGuard:
    def __init__(self, bot):
        self.bot = bot
        self.emoji_deletes = {} # guild_id -> deque of timestamps

    async def on_emoji_delete(self, emoji):
        guild = emoji.guild
        now = time.time()

        if guild.id not in self.emoji_deletes:
            self.emoji_deletes[guild.id] = deque()

        self.emoji_deletes[guild.id].append(now)

        while self.emoji_deletes[guild.id] and now - self.emoji_deletes[guild.id][0] > RAID_THRESHOLD_SEC:
            self.emoji_deletes[guild.id].popleft()

        if len(self.emoji_deletes[guild.id]) >= 3:
            logger.warning(f"Mass emoji deletion detected in guild {guild.id}!")
            event_context = f"Mass emoji deletion detected in guild {guild.name} ({guild.id}). {len(self.emoji_deletes[guild.id])} emojis deleted in {RAID_THRESHOLD_SEC}s."
            ai_verdict = await ask_ai(event_context)
            if ai_verdict and ai_verdict.get("verdict") == "RAID_DETECTED":
                # Restore emojis from snapshot logic would go here
                pass

    async def on_emoji_create(self, emoji):
        # Delete unauthorized emojis
        pass
