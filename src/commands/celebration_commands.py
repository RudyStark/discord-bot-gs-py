import discord
from discord import app_commands
from src.bot.gs_bot import bot
from src.utils.permissions import has_required_role

@bot.tree.command(name="gg", description="Féliciter les participants avec 3 étoiles")
async def congratulate(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True, delete_after=10)
        return

    three_stars = [
        bot.gs_data['players'][user_id]['mention']
        for user_id in bot.gs_data['players']
        if bot.gs_data['stars'].get(user_id, 0) >= 3
    ]

    embed = discord.Embed(
        title="🎉 Félicitations et Remerciements !",
        color=discord.Color.gold()
    )

    if three_stars:
        embed.add_field(
            name="🌟 Performances Exceptionnelles !",
            value=f"Félicitations à nos champions avec 3 étoiles :\n{', '.join(three_stars)}",
            inline=False
        )

    all_participants = [info['mention'] for info in bot.gs_data['players'].values()]
    embed.add_field(
        name="👏 Merci à tous les participants !",
        value=f"Un grand merci à tous pour votre participation :\n{', '.join(all_participants)}",
        inline=False
    )

    await interaction.response.send_message(embed=embed)