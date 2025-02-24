import discord
from datetime import datetime, timedelta
from src.statistics.data_manager import DataManager
from src.statistics.export_manager import ExportManager
from src.bot.gs_bot import bot
from src.utils.embeds import update_gs_message

class EndGSModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Fin de la Guerre Sainte")

        self.guild_name = discord.ui.TextInput(
            label='Nom de la guilde adverse',
            placeholder='Entrez le nom de la guilde',
            required=True,
            max_length=100
        )
        self.add_item(self.guild_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Initialiser les managers
            data_manager = DataManager()
            export_manager = ExportManager()

            # Sauvegarder les données du jour
            success = await data_manager.save_daily_stats(self.guild_name.value)
            if not success:
                await interaction.response.send_message(
                    "❌ Une erreur s'est produite lors de la sauvegarde des données.",
                    ephemeral=True
                )
                return

            # Générer l'export du jour
            today = datetime.now().strftime("%Y-%m-%d")
            daily_report = export_manager.generate_daily_report(today)

            # Vérifier si c'est la fin de la semaine (samedi)
            if datetime.now().weekday() == 5:  # 5 = Samedi
                start_of_week = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                weekly_report = export_manager.generate_weekly_report(start_of_week)
                weekly_msg = "\n✅ Rapport hebdomadaire généré." if weekly_report else ""
            else:
                weekly_msg = ""

            # Vérifier si c'est la fin de la saison (2e samedi)
            season_start = data_manager.get_season_dates()[0]
            if datetime.now().weekday() == 5 and datetime.now().strftime("%Y-%m-%d") == (
                datetime.strptime(season_start, "%Y-%m-%d") + timedelta(days=11)
            ).strftime("%Y-%m-%d"):
                season_report = export_manager.generate_season_report(season_start)
                season_msg = "\n✅ Rapport de saison généré." if season_report else ""
            else:
                season_msg = ""

            # Réinitialiser les données de la GS tout en gardant la liste des joueurs
            players_backup = bot.gs_data['players'].copy()
            message_id_backup = bot.gs_data['message_id']
            check_message_id_backup = bot.gs_data.get('check_message_id')

            # Réinitialiser toutes les données d'actions et statistiques
            bot.gs_data['defenses'] = {}
            bot.gs_data['tests'] = {}
            bot.gs_data['attacks'] = {}
            bot.gs_data['stars'] = {}

            # Restaurer uniquement les données à conserver
            bot.gs_data['players'] = players_backup
            bot.gs_data['message_id'] = message_id_backup
            if check_message_id_backup:
                bot.gs_data['check_message_id'] = check_message_id_backup

            # Mettre à jour l'affichage du tableau
            await update_gs_message(interaction.channel)

            # Envoyer le message de confirmation avec les informations sur les rapports générés
            await interaction.response.send_message(
                f"✅ Données de la GS sauvegardées pour la guilde {self.guild_name.value}."
                f"\n✅ Rapport journalier généré.{weekly_msg}{season_msg}"
                f"\n✅ Le tableau de GS a été réinitialisé pour la prochaine journée.",
                ephemeral=True
            )

        except Exception as e:
            print(f"Erreur lors de la fin de GS : {e}")
            await interaction.response.send_message(
                "❌ Une erreur s'est produite lors de la finalisation de la GS.",
                ephemeral=True
            )