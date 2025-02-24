import discord
from src.bot.gs_bot import bot
from src.utils.embeds import update_gs_message

class PlayerRotationView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Menu unique pour la sélection du joueur
        options = []
        for user_id, player_info in bot.gs_data['players'].items():
            current_status = "Titulaire" if player_info.get('status', 'titulaire') == 'titulaire' else "Remplaçant"
            options.append(
                discord.SelectOption(
                    label=f"{player_info['name']}",
                    value=str(user_id),
                    description=f"Actuellement : {current_status}"
                )
            )

        self.player_select = discord.ui.Select(
            placeholder="Sélectionnez le joueur à changer de statut",
            min_values=1,
            max_values=1,
            options=options
        )

        async def swap_callback(interaction: discord.Interaction):
            try:
                # Conversion string → int de l'ID
                player_id = int(self.player_select.values[0])
                player_info = bot.gs_data['players'][player_id]

                # Changement de statut
                current_status = player_info.get('status', 'titulaire')
                new_status = 'remplacant' if current_status == 'titulaire' else 'titulaire'
                player_info['status'] = new_status

                # Suppression des actions
                for action_type in ['defenses', 'tests', 'attacks']:
                    if player_id in bot.gs_data[action_type]:
                        del bot.gs_data[action_type][player_id]

                await interaction.response.edit_message(
                    content=f"✅ Changement de statut effectué :\n"
                           f"• {player_info['mention']} est maintenant {new_status}",
                    view=None
                )

                await update_gs_message(interaction.channel)

            except Exception as e:
                print(f"Erreur lors du changement de statut : {str(e)}")
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite.",
                    ephemeral=True
                )

        cancel_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Annuler"
        )

        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="❌ Changement de statut annulé.",
                view=None
            )

        self.player_select.callback = swap_callback
        cancel_button.callback = cancel_callback

        self.add_item(self.player_select)
        self.add_item(cancel_button)