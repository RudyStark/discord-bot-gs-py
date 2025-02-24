import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.bot.gs_bot import bot

class DataManager:
    def __init__(self):
        self.base_path = "data"
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Crée la structure des dossiers si elle n'existe pas"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "daily"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "weekly"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "seasonal"), exist_ok=True)

    def get_season_dates(self) -> tuple[str, str]:
        """Calcule les dates de début et fin de la saison actuelle"""
        today = datetime.now()
        # Trouver le lundi le plus récent
        days_since_monday = today.weekday()
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=11)  # 12 jours au total
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    async def save_daily_stats(self, guild_name: str) -> bool:
        """Sauvegarde les statistiques journalières"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_data = {
                "date": today,
                "guild_name": guild_name,
                "participants": []
            }

            for user_id, player_info in bot.gs_data['players'].items():
                # Créer les données du joueur
                player_data = {
                    "id": str(user_id),
                    "name": player_info["name"],
                    "mention": player_info["mention"],
                    "status": player_info.get("status", "titulaire"),
                    "stars": bot.gs_data['stars'].get(user_id, 0),
                    "defense": bot.gs_data['defenses'].get(user_id, None),
                    "test": bot.gs_data['tests'].get(user_id, None),
                    "attack": bot.gs_data['attacks'].get(user_id, None)
                }
                daily_data["participants"].append(player_data)

            # Sauvegarder dans un fichier JSON quotidien
            filename = f"{today}.json"
            filepath = os.path.join(self.base_path, "daily", filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(daily_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Erreur lors de la sauvegarde des stats journalières : {e}")
            return False

    def load_daily_stats(self, date: str) -> Optional[Dict]:
        """Charge les statistiques d'une journée spécifique"""
        try:
            filepath = os.path.join(self.base_path, "daily", f"{date}.json")
            if not os.path.exists(filepath):
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des stats du {date}: {e}")
            return None

    def load_weekly_stats(self, start_date: str) -> List[Dict]:
        """Charge les statistiques d'une semaine"""
        stats = []
        start = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(6):  # 6 jours
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_stats = self.load_daily_stats(date)
            if daily_stats:
                stats.append(daily_stats)

        return stats

    def load_season_stats(self, start_date: str) -> List[Dict]:
        """Charge les statistiques d'une saison (12 jours)"""
        stats = []
        start = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(12):  # 12 jours
            date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_stats = self.load_daily_stats(date)
            if daily_stats:
                stats.append(daily_stats)

        return stats