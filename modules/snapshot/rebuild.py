import discord
from modules.snapshot.capture import load_snapshot
from core.logger import logger

async def rebuild_channels(guild, scope="channels"):
    """
    Diff the live server vs the snapshot (what's missing)
    Recreate ONLY missing channels/roles — never duplicate
    Restore permission overwrites exactly
    """
    snapshot = load_snapshot(guild.id)
    if not snapshot:
        print(f"❌ No snapshot found for guild {guild.id}")
        return False

    report = {
        "channels_recreated": 0,
        "roles_recreated": 0,
        "errors": []
    }

    # Helper function to apply overwrites
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

    # Restore Channels
    existing_channels_names = {channel.name for channel in guild.channels}

    # Recreate Categories first
    categories = {}
    for channel_data in snapshot["channels"]:
        if channel_data["type"] == "category":
            if channel_data["name"] not in existing_channels_names:
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
                # Find the existing category
                cat = discord.utils.get(guild.categories, name=channel_data["name"])
                categories[channel_data["id"]] = cat
                # Optionally restore overwrites for existing categories
                if cat: await apply_overwrites(cat, channel_data["permission_overwrites"], guild)

    # Recreate Text and Voice Channels
    for channel_data in snapshot["channels"]:
        if channel_data["type"] == "category": continue
        if channel_data["name"] not in existing_channels_names:
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

    # Notify owner
    owner = guild.owner
    if owner:
        embed = discord.Embed(
            title="⚔️ SENTINEL Server Rebuild Complete",
            color=discord.Color.green(),
            description=f"✅ Recreated {report['channels_recreated']} channels and categories."
        )
        if report["errors"]:
            embed.add_field(name="⚠️ Issues Encountered", value="\n".join(report["errors"])[:1024])
        try:
            await owner.send(embed=embed)
        except:
            pass

    return report
