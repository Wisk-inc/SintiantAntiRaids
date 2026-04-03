import os
import sys
import traceback
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# --- BUG 1 FIX: Hardcode Termux Path & Force Load ---
TERMUX_PATH = "/data/data/com.termux/files/home/SintiantAntiRaids/.env"
if os.path.exists(TERMUX_PATH):
    load_dotenv(TERMUX_PATH)
else:
    # Fallback to local .env if not on Termux
    load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- BUG 3 FIX: Enable ALL Intents ---
intents = discord.Intents.all()

class SentinelBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None # Using slash commands mostly
        )

    async def setup_hook(self):
        print("--- [SENTINEL STARTUP] ---")

        # List of extensions to load
        extensions = [
            "events.handlers",
            "modules.auth.commands",
            # Add more as they are completed
        ]

        # --- BUG 2 FIX: Detailed Error Printing for Extensions ---
        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ Loaded extension: {ext}")
            except Exception as e:
                print(f"❌ Failed to load extension {ext}!")
                print(f"Error: {e}")
                traceback.print_exc()

        print("--- [EXTENSION LOADING COMPLETE] ---")

    async def on_ready(self):
        print(f"--- [SENTINEL ONLINE] ---")
        print(f"Logged in as: {self.user.name}#{self.user.discriminator}")
        print(f"Bot ID: {self.user.id}")
        print(f"Guilds: {len(self.guilds)}")
        print("--------------------------")

# --- BUG 4 FIX: /sync command ---
bot = SentinelBot()

@bot.tree.command(name="sync", description="Sync slash commands (Owner only)")
async def sync(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Only the server owner can sync commands.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ Successfully synced {len(synced)} slash commands.")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to sync: {e}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN not found in .env!")
        sys.exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start bot: {e}")
        traceback.print_exc()
