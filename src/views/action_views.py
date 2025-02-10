import discord
from src.bot.gs_bot import bot
from src.utils.embeds import update_gs_message
from src.config.constants import DEFENSE_EMOJI, TEST_EMOJI, ATTACK_EMOJI  # Ajout des imports manquants

class ActionView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.action_type = None

    @discord.ui.button(label="Défense", emoji="🛡️", style=discord.ButtonStyle.primary)
    async def defense_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "defense")

    @discord.ui.button(label="Test", emoji="🔍", style=discord.ButtonStyle.primary)
    async def test_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "test")

    @discord.ui.button(label="Attaque", emoji="⚔️", style=discord.ButtonStyle.primary)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_number_select(interaction, "attack")

    @discord.ui.button(label="Reset", emoji="🔄", style=discord.ButtonStyle.danger)
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in bot.gs_data['players']:
            await interaction.response.send_message(
                "❌ Vous n'êtes pas dans la liste des joueurs GS !",
                ephemeral=True
            )
            return

        action_options = [
            discord.SelectOption(label="Défense", value="defense", emoji=DEFENSE_EMOJI),
            discord.SelectOption(label="Test", value="test", emoji=TEST_EMOJI),
            discord.SelectOption(label="Attaque", value="attack", emoji=ATTACK_EMOJI),
            discord.SelectOption(label="Toutes mes actions", value="all", emoji="🔄")
        ]

        select = discord.ui.Select(
            placeholder="Action à réinitialiser",
            min_values=1,
            max_values=1,
            options=action_options
        )

        async def reset_callback(reset_interaction: discord.Interaction):
            try:
                action = select.values[0]
                user_id = reset_interaction.user.id
                message = ""

                if action == "all":
                    if user_id in bot.gs_data['defenses']: del bot.gs_data['defenses'][user_id]
                    if user_id in bot.gs_data['tests']: del bot.gs_data['tests'][user_id]
                    if user_id in bot.gs_data['attacks']: del bot.gs_data['attacks'][user_id]
                    message = "✅ Toutes vos actions ont été réinitialisées."
                elif action == "defense":
                    if user_id in bot.gs_data['defenses']:
                        del bot.gs_data['defenses'][user_id]
                        message = "✅ Votre défense a été réinitialisée."
                    else:
                        message = "ℹ️ Vous n'aviez pas de défense enregistrée."
                elif action == "test":
                    if user_id in bot.gs_data['tests']:
                        del bot.gs_data['tests'][user_id]
                        message = "✅ Votre test a été réinitialisé."
                    else:
                        message = "ℹ️ Vous n'aviez pas de test enregistré."
                elif action == "attack":
                    if user_id in bot.gs_data['attacks']:
                        del bot.gs_data['attacks'][user_id]
                        message = "✅ Votre attaque a été réinitialisée."
                    else:
                        message = "ℹ️ Vous n'aviez pas d'attaque enregistrée."

                await reset_interaction.response.send_message(message, ephemeral=True)
                await update_gs_message(reset_interaction.channel)

            except Exception as e:
                print(f"Erreur dans le reset des actions: {e}")
                await reset_interaction.response.send_message(
                    "❌ Une erreur s'est produite.",
                    ephemeral=True
                )

        select.callback = reset_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message(
            "Sélectionnez l'action à réinitialiser :",
            view=view,
            ephemeral=True
        )

    async def show_number_select(self, interaction: discord.Interaction, action_type: str):
        try:
            self.action_type = action_type
            select = ActionSelect()
            self.clear_items()
            self.add_item(select)

            embed = discord.Embed(
                title=f"Choisissez votre {action_type}",
                description="Sélectionnez une cible entre 1 et 20",
                color=discord.Color.blue()
            )

            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Erreur dans show_number_select: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True, delete_after=10)

class ActionSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=str(i), value=str(i))
            for i in range(1, 21)
        ]
        super().__init__(placeholder="Choisissez une cible", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            view = self.view
            action_value = int(self.values[0])

            if view.action_type == "defense":
                bot.gs_data['defenses'][interaction.user.id] = action_value
                message = f"✅ Défense {action_value} enregistrée."
            elif view.action_type == "test":
                bot.gs_data['tests'][interaction.user.id] = action_value
                message = f"✅ Test {action_value} enregistré."
            else:
                bot.gs_data['attacks'][interaction.user.id] = action_value
                message = f"✅ Attaque {action_value} enregistrée."

            await interaction.response.edit_message(content=message, embed=None, view=None)
            await update_gs_message(interaction.channel)
        except Exception as e:
            print(f"Erreur dans le callback de sélection: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Une erreur s'est produite.", ephemeral=True, delete_after=10)