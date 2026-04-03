import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from tinydb import TinyDB, Query

# --- BUG 5 FIX: Full Auth Cog Implementation ---
class AuthCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Persistence setup
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        self.db_path = os.path.join(data_dir, "auth_registry.json")
        self.db = TinyDB(self.db_path)
        self.registry = self.db.table("registry")

    def is_authorized(self, guild_id, user_id):
        User = Query()
        result = self.registry.get((User.guild_id == guild_id) & (User.user_id == user_id))
        return result is not None

    @app_commands.command(name="authorize", description="Authorize a user (Owner only)")
    async def authorize(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can authorize users.", ephemeral=True)
            return

        if self.is_authorized(interaction.guild.id, member.id):
            await interaction.response.send_message(f"ℹ️ {member.mention} is already authorized.", ephemeral=True)
            return

        self.registry.insert({"guild_id": interaction.guild.id, "user_id": member.id})
        await interaction.response.send_message(f"✅ Authorized {member.mention} successfully.", ephemeral=False)

    @app_commands.command(name="deauthorize", description="Revoke a user's trust (Owner only)")
    async def deauthorize(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can deauthorize users.", ephemeral=True)
            return

        User = Query()
        result = self.registry.remove((User.guild_id == interaction.guild.id) & (User.user_id == member.id))

        if len(result) > 0:
            await interaction.response.send_message(f"✅ Deauthorized {member.mention}.", ephemeral=False)
        else:
            await interaction.response.send_message(f"❌ {member.mention} was not authorized.", ephemeral=True)

    @app_commands.command(name="authorized_list", description="Show all trusted admins")
    async def authorized_list(self, interaction: discord.Interaction):
        User = Query()
        results = self.registry.search(User.guild_id == interaction.guild.id)

        if not results:
            await interaction.response.send_message("ℹ️ No users are currently authorized.")
            return

        mentions = [f"<@{res['user_id']}>" for res in results]
        embed = discord.Embed(
            title="⚔️ SENTINEL Trusted Admins",
            description="\n".join(mentions),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Show bot health and security status")
    async def status(self, interaction: discord.Interaction):
        # Additional logic for status reporting can go here
        embed = discord.Embed(
            title="⚔️ SENTINEL Security Status",
            color=discord.Color.green()
        )
        embed.add_field(name="Bot Status", value="🟢 Online", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Active Guards", value="Channel, Role, Message, Member, Webhook, Emoji", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AuthCog(bot))
