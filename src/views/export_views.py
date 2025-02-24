import discord
import os
from datetime import datetime, timedelta
from src.utils.permissions import has_required_role
from src.statistics.data_manager import DataManager
from src.statistics.export_manager import ExportManager

class ExportSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.export_manager = ExportManager()
        self.export_path = "exports"

    @discord.ui.button(label="Export Journalier", emoji="📅", style=discord.ButtonStyle.primary)
    async def daily_export_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        # Créer un sélecteur pour choisir la date
        select = discord.ui.Select(
            placeholder="Sélectionnez une date pour télécharger l'export",
            min_values=1,
            max_values=1
        )

        # Obtenir les dates à partir d'aujourd'hui et les 7 prochains jours
        today = datetime.now()
        available_dates = []

        # Vérifier s'il y a des rapports quotidiens existants
        for file in os.listdir(self.export_path):
            if file.startswith("arayashiki_daily_report_") and file.endswith(".xlsx"):
                date = file.split("_")[3].split(".")[0]  # Extraire la date
                available_dates.append(date)

        # S'il n'y a pas de rapports existants, afficher les dates futures
        if not available_dates:
            for i in range(7):
                date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                select.add_option(
                    label=f"{date}",
                    value=date,
                    description=f"Générer un rapport pour cette date"
                )
        else:
            # Si des rapports existent, montrer les dates existantes et quelques futures
            sorted_dates = sorted(available_dates, reverse=True)
            latest_date = datetime.strptime(sorted_dates[0], "%Y-%m-%d")

            # Ajouter les dates existantes récentes
            for i, date in enumerate(sorted_dates[:5]):
                select.add_option(
                    label=f"{date}",
                    value=date,
                    description="✅ Disponible"
                )

            # Ajouter quelques dates futures si nécessaire
            for i in range(1, 3):
                future_date = (latest_date + timedelta(days=i)).strftime("%Y-%m-%d")
                if future_date not in sorted_dates:
                    select.add_option(
                        label=f"{future_date}",
                        value=future_date,
                        description="Générer un nouveau rapport"
                    )

        # Ajouter un bouton de téléchargement
        download_button = discord.ui.Button(
            label="Télécharger Excel",
            emoji="📊",
            style=discord.ButtonStyle.success,
            disabled=True,  # Désactivé par défaut
            custom_id="download_button"
        )

        selected_date = None

        async def select_callback(select_interaction: discord.Interaction):
            nonlocal selected_date
            selected_date = select.values[0]

            # Activer le bouton de téléchargement maintenant qu'une date est sélectionnée
            download_button.disabled = False

            # Mettre à jour la vue
            await select_interaction.response.edit_message(
                content=f"📅 Date sélectionnée : {selected_date}",
                view=view
            )

        async def download_callback(download_interaction: discord.Interaction):
            if not selected_date:
                await download_interaction.response.send_message(
                    "❌ Veuillez d'abord sélectionner une date.",
                    ephemeral=True
                )
                return

            try:
                # Génération direct en Excel
                filepath = self.export_manager.generate_daily_report(selected_date, "xlsx")
                filename = f"arayashiki_daily_report_{selected_date}.xlsx"

                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as file:
                        await download_interaction.response.send_message(
                            f"📊 Export journalier du {selected_date} (Excel)",
                            file=discord.File(file, filename),
                            ephemeral=True
                        )
                else:
                    await download_interaction.response.send_message(
                        f"❌ Impossible de générer l'export Excel pour le {selected_date}.",
                        ephemeral=True
                    )
            except Exception as e:
                print(f"Erreur lors de la génération de l'export : {e}")
                await download_interaction.response.send_message(
                    f"❌ Une erreur s'est produite lors de la génération de l'export : {str(e)}",
                    ephemeral=True
                )

        select.callback = select_callback
        download_button.callback = download_callback

        view = discord.ui.View()
        view.add_item(select)
        view.add_item(download_button)

        await interaction.response.send_message(
            "📅 Sélectionnez une date puis cliquez pour télécharger le rapport Excel :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Export Hebdomadaire", emoji="📆", style=discord.ButtonStyle.primary)
    async def weekly_export_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        # Créer un sélecteur pour choisir la semaine
        select = discord.ui.Select(
            placeholder="Sélectionnez une semaine",
            min_values=1,
            max_values=1
        )

        # Trouver les exports hebdomadaires existants
        available_weeks = []
        for file in os.listdir(self.export_path):
            if file.startswith("arayashiki_weekly_report_") and file.endswith(".xlsx"):
                parts = file.split("_")
                if len(parts) >= 6:  # s'assurer que le format est correct
                    start_date = parts[3]
                    available_weeks.append(start_date)

        # S'il n'y a pas d'exports existants, proposer les semaines futures
        if not available_weeks:
            # Trouver le lundi le plus récent
            today = datetime.now()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday)

            for i in range(4):  # 4 semaines
                start_date = (last_monday + timedelta(weeks=i)).strftime("%Y-%m-%d")
                end_date = (last_monday + timedelta(weeks=i, days=5)).strftime("%Y-%m-%d")
                select.add_option(
                    label=f"Semaine du {start_date} au {end_date}",
                    value=start_date,
                    description="Nouvelle semaine"
                )
        else:
            # Ajouter les semaines existantes et futures
            sorted_weeks = sorted(available_weeks, reverse=True)
            latest_week_start = datetime.strptime(sorted_weeks[0], "%Y-%m-%d")

            # Ajouter les semaines existantes
            for i, start_date in enumerate(sorted_weeks[:4]):
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
                select.add_option(
                    label=f"Semaine du {start_date} au {end_date}",
                    value=start_date,
                    description="✅ Disponible"
                )

            # Ajouter la prochaine semaine (après une semaine de repos)
            next_week_start = (latest_week_start + timedelta(days=19)).strftime("%Y-%m-%d")  # 12 jours + 7 jours de repos
            next_week_end = (datetime.strptime(next_week_start, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
            select.add_option(
                label=f"Semaine du {next_week_start} au {next_week_end}",
                value=next_week_start,
                description="Prochaine semaine"
            )

        # Ajouter un bouton de téléchargement
        download_button = discord.ui.Button(
            label="Télécharger Excel",
            emoji="📊",
            style=discord.ButtonStyle.success,
            disabled=True,  # Désactivé par défaut
            custom_id="download_button"
        )

        selected_start_date = None

        async def select_callback(select_interaction: discord.Interaction):
            nonlocal selected_start_date
            selected_start_date = select.values[0]

            # Activer le bouton de téléchargement maintenant qu'une date est sélectionnée
            download_button.disabled = False

            # Calculer la date de fin
            end_date = (datetime.strptime(selected_start_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")

            # Mettre à jour la vue
            await select_interaction.response.edit_message(
                content=f"📆 Semaine sélectionnée : du {selected_start_date} au {end_date}",
                view=view
            )

        async def download_callback(download_interaction: discord.Interaction):
            if not selected_start_date:
                await download_interaction.response.send_message(
                    "❌ Veuillez d'abord sélectionner une semaine.",
                    ephemeral=True
                )
                return

            try:
                end_date = (datetime.strptime(selected_start_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
                filepath = self.export_manager.generate_weekly_report(selected_start_date, "xlsx")
                filename = f"arayashiki_weekly_report_{selected_start_date}_to_{end_date}.xlsx"

                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as file:
                        await download_interaction.response.send_message(
                            f"📊 Export hebdomadaire du {selected_start_date} au {end_date} (Excel)",
                            file=discord.File(file, filename),
                            ephemeral=True
                        )
                else:
                    await download_interaction.response.send_message(
                        f"❌ Impossible de générer l'export Excel pour la semaine du {selected_start_date} au {end_date}.",
                        ephemeral=True
                    )
            except Exception as e:
                print(f"Erreur lors de la génération de l'export hebdomadaire : {e}")
                await download_interaction.response.send_message(
                    f"❌ Une erreur s'est produite lors de la génération de l'export : {str(e)}",
                    ephemeral=True
                )

        select.callback = select_callback
        download_button.callback = download_callback

        view = discord.ui.View()
        view.add_item(select)
        view.add_item(download_button)

        await interaction.response.send_message(
            "📆 Sélectionnez une semaine puis cliquez pour télécharger le rapport Excel :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Export Saisonnier", emoji="📈", style=discord.ButtonStyle.primary)
    async def season_export_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.",
                ephemeral=True
            )
            return

        # Créer un sélecteur pour choisir la saison
        select = discord.ui.Select(
            placeholder="Sélectionnez une saison",
            min_values=1,
            max_values=1
        )

        # Trouver les exports saisonniers existants
        available_seasons = []
        for file in os.listdir(self.export_path):
            if file.startswith("arayashiki_season_report_") and file.endswith(".xlsx"):
                parts = file.split("_")
                if len(parts) >= 6:  # s'assurer que le format est correct
                    start_date = parts[3]
                    available_seasons.append(start_date)

        # S'il n'y a pas d'exports existants, proposer les saisons futures basées sur le calendrier
        if not available_seasons:
            # Obtenir les dates de la saison actuelle
            season_start, season_end = self.data_manager.get_season_dates()
            current_start = datetime.strptime(season_start, "%Y-%m-%d")

            for i in range(3):  # 3 saisons (actuelle + 2 futures)
                # Une saison = 12 jours, puis 7 jours de repos
                start_date = (current_start + timedelta(days=i*(12+7))).strftime("%Y-%m-%d")
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")
                select.add_option(
                    label=f"Saison du {start_date} au {end_date}",
                    value=start_date,
                    description="Nouvelle saison"
                )
        else:
            # Ajouter les saisons existantes et futures
            sorted_seasons = sorted(available_seasons, reverse=True)
            latest_season_start = datetime.strptime(sorted_seasons[0], "%Y-%m-%d")

            # Ajouter les saisons existantes
            for i, start_date in enumerate(sorted_seasons[:3]):
                end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")
                select.add_option(
                    label=f"Saison du {start_date} au {end_date}",
                    value=start_date,
                    description="✅ Disponible"
                )

            # Ajouter la prochaine saison (après la période de repos)
            next_season_start = (latest_season_start + timedelta(days=19)).strftime("%Y-%m-%d")  # 12 jours + 7 jours de repos
            next_season_end = (datetime.strptime(next_season_start, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")
            select.add_option(
                label=f"Saison du {next_season_start} au {next_season_end}",
                value=next_season_start,
                description="Prochaine saison"
            )

        # Ajouter un bouton de téléchargement
        download_button = discord.ui.Button(
            label="Télécharger Excel",
            emoji="📊",
            style=discord.ButtonStyle.success,
            disabled=True,  # Désactivé par défaut
            custom_id="download_button"
        )

        selected_start_date = None

        async def select_callback(select_interaction: discord.Interaction):
            nonlocal selected_start_date
            selected_start_date = select.values[0]

            # Activer le bouton de téléchargement maintenant qu'une date est sélectionnée
            download_button.disabled = False

            # Calculer la date de fin
            end_date = (datetime.strptime(selected_start_date, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")

            # Mettre à jour la vue
            await select_interaction.response.edit_message(
                content=f"📈 Saison sélectionnée : du {selected_start_date} au {end_date}",
                view=view
            )

        async def download_callback(download_interaction: discord.Interaction):
            if not selected_start_date:
                await download_interaction.response.send_message(
                    "❌ Veuillez d'abord sélectionner une saison.",
                    ephemeral=True
                )
                return

            try:
                end_date = (datetime.strptime(selected_start_date, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")
                filepath = self.export_manager.generate_season_report(selected_start_date, "xlsx")
                filename = f"arayashiki_season_report_{selected_start_date}_to_{end_date}.xlsx"

                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as file:
                        await download_interaction.response.send_message(
                            f"📈 Export saisonnier du {selected_start_date} au {end_date} (Excel)",
                            file=discord.File(file, filename),
                            ephemeral=True
                        )
                else:
                    await download_interaction.response.send_message(
                        f"❌ Impossible de générer l'export Excel pour la saison du {selected_start_date} au {end_date}.",
                        ephemeral=True
                    )
            except Exception as e:
                print(f"Erreur lors de la génération de l'export saisonnier : {e}")
                await download_interaction.response.send_message(
                    f"❌ Une erreur s'est produite lors de la génération de l'export : {str(e)}",
                    ephemeral=True
                )

        select.callback = select_callback
        download_button.callback = download_callback

        view = discord.ui.View()
        view.add_item(select)
        view.add_item(download_button)

        await interaction.response.send_message(
            "📈 Sélectionnez une saison puis cliquez pour télécharger le rapport Excel :",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Retour", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Importer ici pour éviter les imports circulaires
        from src.views.admin_views import GSManagementView

        view = GSManagementView()
        embed = discord.Embed(
            title="📊 Gestion de la GS",
            description="Sélectionnez une action à effectuer",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)