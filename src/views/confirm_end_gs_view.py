import discord

class ConfirmEndGSView(discord.ui.View):
    def __init__(self, modal_class):
        super().__init__()
        self.modal_class = modal_class

    @discord.ui.button(label="Oui, terminer la GS", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(self.modal_class())

    @discord.ui.button(label="Non, annuler", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="❌ Fin de GS annulée.",
            view=None
        )