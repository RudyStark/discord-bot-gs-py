import os
import xlsxwriter
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .data_manager import DataManager
from .stats_calculator import StatsCalculator

class ExportManager:
    def __init__(self):
        self.data_manager = DataManager()
        self.stats_calculator = StatsCalculator()
        self.export_path = "exports"
        os.makedirs(self.export_path, exist_ok=True)

    def generate_daily_report(self, date: str, format_type: str = "xlsx") -> Optional[str]:
        """
        Génère un rapport journalier au format Excel

        Args:
            date: Date du rapport au format YYYY-MM-DD
            format_type: "xlsx" uniquement (paramètre gardé pour compatibilité)

        Returns:
            Le chemin vers le fichier généré ou None en cas d'échec
        """
        daily_data = self.data_manager.load_daily_stats(date)
        if not daily_data:
            return None

        return self._generate_daily_excel(daily_data, date)

    def _generate_daily_excel(self, daily_data: Dict, date: str) -> str:
        """Génère un rapport journalier au format Excel avec des cellules plus grandes"""
        filename = f"arayashiki_daily_report_{date}.xlsx"
        filepath = os.path.join(self.export_path, filename)

        # Créer un nouveau classeur Excel
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet("Rapport Journalier")

        # Formats pour l'en-tête et les données
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#4B8BBE',
            'border': 1,
            'font_color': 'white',
            'text_wrap': True,
            'font_size': 12
        })

        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
            'font_size': 11
        })

        # En-tête
        headers = [
            "Date", "Guilde adverse", "Joueur", "Statut",
            "Étoiles", "Attaques réussies", "Taux de réussite"
        ]

        # Définir des largeurs de colonnes plus grandes
        column_widths = {
            0: 12,   # Date
            1: 20,   # Guilde adverse
            2: 25,   # Joueur
            3: 15,   # Statut
            4: 10,   # Étoiles
            5: 18,   # Attaques réussies
            6: 18    # Taux de réussite
        }

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            worksheet.set_column(col_num, col_num, column_widths.get(col_num, 15))

        # Définir la hauteur de ligne pour l'en-tête et toutes les lignes de données
        worksheet.set_row(0, 30)  # Hauteur de l'en-tête

        # Données
        row = 1
        for participant in daily_data["participants"]:
            # Définir une hauteur de ligne standard pour toutes les lignes de données
            worksheet.set_row(row, 25)  # Hauteur des lignes de données

            stars = participant.get("stars", 0)
            attacks_success = StatsCalculator.calculate_attack_success(stars)
            success_rate = StatsCalculator.calculate_success_rate(
                stars,
                StatsCalculator.MAX_STARS_PER_DAY if participant["status"] == "titulaire" else 0
            )

            worksheet.write(row, 0, date, cell_format)
            worksheet.write(row, 1, daily_data["guild_name"], cell_format)
            worksheet.write(row, 2, participant["name"], cell_format)
            worksheet.write(row, 3, participant["status"], cell_format)
            worksheet.write(row, 4, stars, cell_format)
            worksheet.write(row, 5, attacks_success, cell_format)
            worksheet.write(row, 6, f"{success_rate:.2f}%", cell_format)

            row += 1

        # Ajuster la mise en page
        worksheet.autofilter(0, 0, row-1, len(headers)-1)
        worksheet.freeze_panes(1, 0)

        workbook.close()
        return filepath

    def generate_weekly_report(self, start_date: str, format_type: str = "xlsx") -> Optional[str]:
        """
        Génère un rapport hebdomadaire

        Args:
            start_date: Date de début au format YYYY-MM-DD
            format_type: "xlsx" uniquement (paramètre gardé pour compatibilité)

        Returns:
            Le chemin vers le fichier généré ou None en cas d'échec
        """
        weekly_data = self.data_manager.load_weekly_stats(start_date)
        if not weekly_data:
            return None

        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")

        return self._generate_weekly_excel(weekly_data, start_date, end_date)

    def _generate_weekly_excel(self, weekly_data: List[Dict], start_date: str, end_date: str) -> str:
        """Génère un rapport hebdomadaire au format Excel avec des cellules plus grandes"""
        filename = f"arayashiki_weekly_report_{start_date}_to_{end_date}.xlsx"
        filepath = os.path.join(self.export_path, filename)

        all_players_stats = self.stats_calculator.calculate_all_players_stats(weekly_data)

        # Créer un nouveau classeur Excel
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet("Rapport Hebdomadaire")

        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#4B8BBE',
            'border': 1,
            'font_color': 'white',
            'text_wrap': True,
            'font_size': 12
        })

        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
            'font_size': 11
        })

        # En-tête
        headers = [
            "Joueur",
            "Total Étoiles",
            "Attaques Réussies",
            "Taux de Réussite Global",
            "Taux de Réussite Attaques",
            "Moyenne Étoiles/Jour",
            "Jours comme Titulaire",
            "Détail par Jour"
        ]

        # Définir des largeurs de colonnes personnalisées
        column_widths = {
            0: 25,   # Joueur
            1: 12,   # Total Étoiles
            2: 18,   # Attaques Réussies
            3: 20,   # Taux de Réussite Global
            4: 20,   # Taux de Réussite Attaques
            5: 18,   # Moyenne Étoiles/Jour
            6: 20,   # Jours comme Titulaire
            7: 50    # Détail par Jour
        }

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            worksheet.set_column(col_num, col_num, column_widths.get(col_num, 18))

        # Définir la hauteur de l'en-tête
        worksheet.set_row(0, 30)

        # Données
        row = 1
        for player in all_players_stats:
            # Définir une hauteur de ligne flexible pour toutes les lignes de données
            worksheet.set_row(row, 35)  # Plus grande hauteur pour le détail

            daily_details = []
            for perf in player["daily_performances"]:
                daily_details.append(
                    f"{perf['date']}: {perf['stars']}⭐ ({perf['attacks_success']}) vs {perf['guild']}"
                )

            worksheet.write(row, 0, player["name"], cell_format)
            worksheet.write(row, 1, player["total_stars"], cell_format)
            worksheet.write(row, 2, f"{player['successful_attacks']}/{player['total_attacks']}", cell_format)
            worksheet.write(row, 3, f"{player['success_rate']:.2f}%", cell_format)
            worksheet.write(row, 4, f"{player['attack_success_rate']:.2f}%", cell_format)
            worksheet.write(row, 5, f"{player['avg_stars_per_day']:.2f}", cell_format)
            worksheet.write(row, 6, player["days_as_titulaire"], cell_format)
            worksheet.write(row, 7, " | ".join(daily_details), cell_format)

            row += 1

        # Ajuster la mise en page
        worksheet.autofilter(0, 0, row-1, len(headers)-1)
        worksheet.freeze_panes(1, 0)

        workbook.close()
        return filepath

    def generate_season_report(self, start_date: str, format_type: str = "xlsx") -> Optional[str]:
        """
        Génère un rapport saisonnier

        Args:
            start_date: Date de début au format YYYY-MM-DD
            format_type: "xlsx" uniquement (paramètre gardé pour compatibilité)

        Returns:
            Le chemin vers le fichier généré ou None en cas d'échec
        """
        season_data = self.data_manager.load_season_stats(start_date)
        if not season_data:
            return None

        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=11)).strftime("%Y-%m-%d")

        return self._generate_season_excel(season_data, start_date, end_date)

    def _generate_season_excel(self, season_data: List[Dict], start_date: str, end_date: str) -> str:
        """Génère un rapport saisonnier au format Excel avec des cellules plus grandes"""
        filename = f"arayashiki_season_report_{start_date}_to_{end_date}.xlsx"
        filepath = os.path.join(self.export_path, filename)

        all_players_stats = self.stats_calculator.calculate_all_players_stats(season_data)

        # Créer un nouveau classeur Excel
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet("Rapport Saisonnier")

        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#4B8BBE',
            'border': 1,
            'font_color': 'white',
            'text_wrap': True,
            'font_size': 12
        })

        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
            'font_size': 11
        })

        # En-tête
        headers = [
            "Rang",
            "Joueur",
            "Total Étoiles",
            "Maximum Possible",
            "Attaques Réussies",
            "Taux de Réussite Global",
            "Taux de Réussite Attaques",
            "Moyenne Étoiles/Jour",
            "Jours comme Titulaire"
        ]

        # Définir des largeurs de colonnes personnalisées
        column_widths = {
            0: 8,    # Rang
            1: 25,   # Joueur
            2: 15,   # Total Étoiles
            3: 18,   # Maximum Possible
            4: 18,   # Attaques Réussies
            5: 20,   # Taux de Réussite Global
            6: 22,   # Taux de Réussite Attaques
            7: 22,   # Moyenne Étoiles/Jour
            8: 20    # Jours comme Titulaire
        }

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)
            worksheet.set_column(col_num, col_num, column_widths.get(col_num, 18))

        # Définir la hauteur de l'en-tête
        worksheet.set_row(0, 30)

        # Données
        row = 1
        for rank, player in enumerate(all_players_stats, 1):
            # Définir une hauteur de ligne standard pour toutes les lignes de données
            worksheet.set_row(row, 25)

            max_possible = player["days_as_titulaire"] * StatsCalculator.MAX_STARS_PER_DAY

            worksheet.write(row, 0, rank, cell_format)
            worksheet.write(row, 1, player["name"], cell_format)
            worksheet.write(row, 2, player["total_stars"], cell_format)
            worksheet.write(row, 3, max_possible, cell_format)
            worksheet.write(row, 4, f"{player['successful_attacks']}/{player['total_attacks']}", cell_format)
            worksheet.write(row, 5, f"{player['success_rate']:.2f}%", cell_format)
            worksheet.write(row, 6, f"{player['attack_success_rate']:.2f}%", cell_format)
            worksheet.write(row, 7, f"{player['avg_stars_per_day']:.2f}", cell_format)
            worksheet.write(row, 8, player["days_as_titulaire"], cell_format)

            row += 1

        # Ajuster la mise en page
        worksheet.autofilter(0, 0, row-1, len(headers)-1)
        worksheet.freeze_panes(1, 0)

        workbook.close()
        return filepath