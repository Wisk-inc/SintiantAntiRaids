import discord
from discord.ext import commands
from discord import app_commands
from core.bot import SentinelBot
from modules.auth.authorization import AuthorizationSystem
from modules.snapshot.capture import capture_guild_snapshot
from modules.snapshot.rebuild import rebuild_from_snapshot

class SecurityCommands(commands.Cog):
    def __init__(self, bot: SentinelBot):
        self.bot = bot
        self.auth = AuthorizationSystem()

    @app_commands.command(name="authorize", description="Authorize a user (Owner only)")
    async def authorize(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Only the server owner can authorize users.", ephemeral=True)
            return

        if self.auth.authorize_user(interaction.guild.id, user.id):
            await interaction.response.send_message(f"Authorized {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} is already authorized.", ephemeral=True)

    @app_commands.command(name="deauthorize", description="Deauthorize a user (Owner only)")
    async def deauthorize(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Only the server owner can deauthorize users.", ephemeral=True)
            return

        if self.auth.deauthorize_user(interaction.guild.id, user.id):
            await interaction.response.send_message(f"Deauthorized {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention} is not authorized.", ephemeral=True)

    @app_commands.command(name="authorized_list", description="Show all authorized users")
    async def authorized_list(self, interaction: discord.Interaction):
        authorized_ids = self.auth.get_authorized_users(interaction.guild.id)
        if not authorized_ids:
            await interaction.response.send_message("No authorized users found (excluding owner).")
            return

        mentions = [f"<@{uid}>" for uid in authorized_ids]
        await interaction.response.send_message(f"Authorized users: {', '.join(mentions)}")

    @app_commands.command(name="snapshot", description="Force a server snapshot")
    async def snapshot(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id and not self.auth.is_authorized(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message("You are not authorized to trigger a snapshot.", ephemeral=True)
            return

        capture_guild_snapshot(interaction.guild)
        await interaction.response.send_message("Snapshot captured successfully.", ephemeral=True)

    @app_commands.command(name="status", description="Show bot status")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"SENTINEL Status: Online. Guild ID: {interaction.guild.id}")

async def setup(bot):
    await bot.add_cog(SecurityCommands(bot))
