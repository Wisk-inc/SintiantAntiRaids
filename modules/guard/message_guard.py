import time
from collections import deque
from core.config import MSG_CACHE_SIZE, RAID_THRESHOLD_SEC
from ai.brain import ask_ai
import json
import os
from core.logger import logger

class MessageGuard:
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = {} # channel_id -> deque of message data
        self.everyone_pings = {} # guild_id -> user_id -> deque of timestamps

    async def on_message(self, message):
        if message.author.bot: return

        channel_id = message.channel.id
        if channel_id not in self.message_cache:
            self.message_cache[channel_id] = deque(maxlen=MSG_CACHE_SIZE)

        msg_data = {
            "id": message.id,
            "author": str(message.author),
            "author_id": message.author.id,
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "attachments": [a.url for a in message.attachments]
        }
        self.message_cache[channel_id].append(msg_data)

        # @everyone ping detection
        if message.mention_everyone:
            guild_id = message.guild.id
            user_id = message.author.id
            now = time.time()

            if guild_id not in self.everyone_pings:
                self.everyone_pings[guild_id] = {}
            if user_id not in self.everyone_pings[guild_id]:
                self.everyone_pings[guild_id][user_id] = deque()

            self.everyone_pings[guild_id][user_id].append(now)

            # Clean up
            while self.everyone_pings[guild_id][user_id] and now - self.everyone_pings[guild_id][user_id][0] > 60:
                self.everyone_pings[guild_id][user_id].popleft()

            if len(self.everyone_pings[guild_id][user_id]) >= 2:
                # Everyone spam detected!
                logger.warning(f"Everyone spam detected from {message.author} in {message.guild.name}!")
                event_context = f"@everyone spam detected from user {message.author.name} (ID: {user_id}) in guild {message.guild.name} ({guild_id}). {len(self.everyone_pings[guild_id][user_id])} pings in 60s."
                ai_verdict = await ask_ai(event_context)
                if ai_verdict and ai_verdict.get("verdict") in ["RAID_DETECTED", "SUSPICIOUS"]:
                    for action in ai_verdict.get("actions", []):
                        if action.type == "BAN" and action.params.get("target") == str(user_id):
                            await message.guild.ban(message.author, reason=action.params.get("reason", "SENTINEL Anti-Spam"))
                            # Notify owner...

    async def on_bulk_message_delete(self, messages):
        # Bundle cached messages into JSON and send to owner
        pass
