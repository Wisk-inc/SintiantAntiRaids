import discord
from modules.snapshot.capture import load_snapshot
from core.logger import logger

async def rebuild_from_snapshot(guild, scope="all"):
    """
    Diff the live server vs the snapshot (what's missing)
    Recreate ONLY missing channels/roles — never duplicate
    Restore permission overwrites exactly
    """
    snapshot = load_snapshot(guild.id)
    if not snapshot:
        logger.error(f"No snapshot found for guild {guild.id}")
        return False

    report = {
        "channels_recreated": 0,
        "roles_recreated": 0,
        "errors": []
    }

    # 1. Restore Roles
    if scope in ["all", "roles"]:
        existing_roles = {role.name: role for role in guild.roles}
        for role_data in sorted(snapshot["roles"], key=lambda r: r["position"]):
            if role_data["name"] == "@everyone":
                # Update @everyone permissions
                everyone_role = guild.default_role
                await everyone_role.edit(permissions=discord.Permissions(role_data["permissions"]))
                continue

            if role_data["name"] not in existing_roles:
                try:
                    await guild.create_role(
                        name=role_data["name"],
                        color=discord.Color(role_data["color"]),
                        permissions=discord.Permissions(role_data["permissions"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"],
                        reason="SENTINEL Snapshot Rebuild"
                    )
                    report["roles_recreated"] += 1
                except Exception as e:
                    report["errors"].append(f"Error recreating role {role_data['name']}: {e}")

    # 2. Restore Channels
    if scope in ["all", "channels"]:
        existing_channels = {channel.name: channel for channel in guild.channels}
        # First recreate categories
        categories = {}
        for channel_data in snapshot["channels"]:
            if channel_data["type"] == "category":
                if channel_data["name"] not in existing_channels:
                    try:
                        new_cat = await guild.create_category(
                            name=channel_data["name"],
                            position=channel_data["position"],
                            reason="SENTINEL Snapshot Rebuild"
                        )
                        categories[channel_data["id"]] = new_cat
                        report["channels_recreated"] += 1
                        await apply_overwrites(new_cat, channel_data["permission_overwrites"], guild)
                    except Exception as e:
                        report["errors"].append(f"Error recreating category {channel_data['name']}: {e}")
                else:
                    cat = existing_channels[channel_data["name"]]
                    categories[channel_data["id"]] = cat
                    await apply_overwrites(cat, channel_data["permission_overwrites"], guild)

        # Then recreate other channels
        for channel_data in snapshot["channels"]:
            if channel_data["type"] == "category": continue
            if channel_data["name"] not in existing_channels:
                try:
                    parent = categories.get(channel_data["parent_id"])
                    new_channel = None
                    if channel_data["type"] == "text":
                        new_channel = await guild.create_text_channel(
                            name=channel_data["name"],
                            category=parent,
                            position=channel_data["position"],
                            reason="SENTINEL Snapshot Rebuild"
                        )
                    elif channel_data["type"] == "voice":
                        new_channel = await guild.create_voice_channel(
                            name=channel_data["name"],
                            category=parent,
                            position=channel_data["position"],
                            reason="SENTINEL Snapshot Rebuild"
                        )

                    if new_channel:
                        report["channels_recreated"] += 1
                        await apply_overwrites(new_channel, channel_data["permission_overwrites"], guild)

                except Exception as e:
                    report["errors"].append(f"Error recreating channel {channel_data['name']}: {e}")
            else:
                # Channel exists, just restore permissions
                channel = existing_channels[channel_data["name"]]
                await apply_overwrites(channel, channel_data["permission_overwrites"], guild)

    return report

async def apply_overwrites(channel, overwrites_data, guild):
    overwrites = {}
    for ov_data in overwrites_data:
        target = None
        if ov_data["type"] == "role":
            target = discord.utils.get(guild.roles, id=ov_data["id"])
        else:
            target = guild.get_member(ov_data["id"])

        if target:
            overwrites[target] = discord.PermissionOverwrite.from_pair(
                discord.Permissions(ov_data["allow"]),
                discord.Permissions(ov_data["deny"])
            )

    if overwrites:
        try:
            await channel.edit(overwrites=overwrites)
        except Exception as e:
            logger.error(f"Error applying overwrites to {channel.name}: {e}")
