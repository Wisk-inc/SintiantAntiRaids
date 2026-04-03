import discord
from core.logger import logger

async def send_incident_report(guild, ai_verdict):
    """
    DM owner with AI-written incident report
    """
    owner = guild.owner
    if not owner:
        logger.error(f"Guild {guild.name} ({guild.id}) has no owner.")
        return

    embed = discord.Embed(
        title="🚨 SENTINEL INCIDENT REPORT",
        color=discord.Color.red()
    )
    embed.add_field(name="Threat Level", value=f"[{ai_verdict.get('threat_level', 'N/A')}/10]", inline=True)
    embed.add_field(name="Verdict", value=ai_verdict.get("verdict", "N/A"), inline=True)
    embed.add_field(name="Trigger", value=ai_verdict.get("explanation", "N/A"), inline=False)

    actions_taken = ""
    for action in ai_verdict.get("actions", []):
        actions_taken += f"• {action.type}: {action.params}\n"

    if actions_taken:
        embed.add_field(name="Actions Taken", value=actions_taken, inline=False)

    try:
        await owner.send(embed=embed)
    except Exception as e:
        logger.error(f"Error sending DM to owner {owner.id}: {e}")
