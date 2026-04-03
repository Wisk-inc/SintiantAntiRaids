import discord
from ai.brain import ask_ai
from core.logger import logger
from modules.auth.authorization import AuthorizationSystem

class WebhookGuard:
    def __init__(self, bot):
        self.bot = bot
        self.auth = AuthorizationSystem()

    async def on_webhook_update(self, channel):
        # Discord doesn't have on_webhook_create, instead on_webhooks_update
        guild = channel.guild
        try:
            webhooks = await channel.webhooks()
            # This is tricky because we don't know who created it without audit logs
            # For simplicity, if unauth webhook created, AI consult or hard delete
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
                if entry.target.channel.id == channel.id:
                    creator = entry.user
                    if not self.auth.is_authorized(guild.id, creator.id) and creator.id != guild.owner_id:
                        logger.warning(f"Unauthorized webhook created in {channel.name} by {creator.name}")
                        await entry.target.delete(reason="Unauthorized webhook creation")
                        await creator.ban(reason="Unauthorized webhook creation")
                        # AI consult for report
                        event_context = f"Unauthorized webhook created by {creator.name} (ID: {creator.id}) in guild {guild.name} ({guild.id}). Webhook deleted and user banned."
                        await ask_ai(event_context)
        except Exception as e:
            logger.error(f"Error checking webhooks in {channel.name}: {e}")
