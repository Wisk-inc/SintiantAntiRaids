import discord
import time
import json
import os
from core.logger import logger

def save_snapshot(guild):
    """
    Captures a complete image of the server: every channel, category, role,
    permission overwrite, emoji, sticker.
    """
    snapshot = {
        "timestamp": time.time(),
        "guild_id": guild.id,
        "server_name": guild.name,
        "icon": str(guild.icon.url) if guild.icon else None,
        "channels": [],
        "roles": [],
        "emojis": [],
        "stickers": []
    }

    # Channels and Overwrites
    for channel in guild.channels:
        channel_data = {
            "id": channel.id,
            "name": channel.name,
            "type": channel.type.name,
            "position": channel.position,
            "parent_id": channel.category_id,
            "permission_overwrites": []
        }
        for target, overwrite in channel.overwrites.items():
            allow, deny = overwrite.pair()
            channel_data["permission_overwrites"].append({
                "id": target.id,
                "type": "role" if isinstance(target, discord.Role) else "member",
                "allow": allow.value,
                "deny": deny.value
            })
        snapshot["channels"].append(channel_data)

    # Roles
    for role in guild.roles:
        snapshot["roles"].append({
            "id": role.id,
            "name": role.name,
            "color": role.color.value,
            "permissions": role.permissions.value,
            "position": role.position,
            "mentionable": role.mentionable,
            "hoist": role.hoist
        })

    # Emojis
    for emoji in guild.emojis:
        snapshot["emojis"].append({
            "id": emoji.id,
            "name": emoji.name,
            "animated": emoji.animated
        })

    # Save to disk
    os.makedirs("data/snapshots", exist_ok=True)
    with open(f"data/snapshots/{guild.id}.json", "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"✅ Captured snapshot for guild: {guild.name}")
    return snapshot

def load_snapshot(guild_id):
    try:
        with open(f"data/snapshots/{guild_id}.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
