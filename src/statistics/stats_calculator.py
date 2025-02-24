from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class StatsCalculator:
    MAX_STARS_PER_DAY = 6  # 2 attaques × 3 étoiles

    @staticmethod
    def calculate_success_rate(stars: int, max_stars: int) -> float:
        """Calcule le taux de réussite"""
        if max_stars == 0:
            return 0.0
        return (stars / max_stars) * 100

    @staticmethod
    def calculate_attack_success(stars: int) -> str:
        """Calcule le nombre d'attaques réussies basé sur les étoiles"""
        if stars == 0:
            return "0/2 attaques"
        elif stars <= 3:
            return "1/2 attaques"
        else:
            return "2/2 attaques"

    @staticmethod
    def calculate_player_stats(data: List[Dict], player_id: str) -> Dict:
        """Calcule les statistiques d'un joueur sur plusieurs jours"""
        total_stars = 0
        days_as_titulaire = 0
        daily_performances = []
        successful_attacks = 0
        total_attacks = 0

        for daily_data in data:
            for participant in daily_data["participants"]:
                if participant["id"] == player_id:
                    if participant["status"] == "titulaire":
                        days_as_titulaire += 1
                        stars = participant.get("stars", 0)
                        total_stars += stars

                        # Compter les attaques réussies
                        if stars > 0:
                            successful_attacks += (stars + 2) // 3  # Arrondi supérieur
                        total_attacks += 2  # 2 attaques possibles par jour

                        daily_performances.append({
                            "date": daily_data["date"],
                            "stars": stars,
                            "guild": daily_data["guild_name"],
                            "attacks_success": StatsCalculator.calculate_attack_success(stars)
                        })

        max_stars = days_as_titulaire * StatsCalculator.MAX_STARS_PER_DAY
        success_rate = StatsCalculator.calculate_success_rate(total_stars, max_stars)
        attack_success_rate = StatsCalculator.calculate_success_rate(successful_attacks, total_attacks)

        return {
            "total_stars": total_stars,
            "days_as_titulaire": days_as_titulaire,
            "success_rate": success_rate,
            "attack_success_rate": attack_success_rate,
            "successful_attacks": successful_attacks,
            "total_attacks": total_attacks,
            "daily_performances": daily_performances,
            "avg_stars_per_day": total_stars / days_as_titulaire if days_as_titulaire > 0 else 0
        }

    @staticmethod
    def calculate_all_players_stats(data: List[Dict]) -> List[Dict]:
        """Calcule les statistiques pour tous les joueurs"""
        player_stats = {}

        # Collecter tous les joueurs uniques
        player_ids = set()
        for daily_data in data:
            for participant in daily_data["participants"]:
                player_ids.add(participant["id"])

        # Calculer les stats pour chaque joueur
        for player_id in player_ids:
            stats = StatsCalculator.calculate_player_stats(data, player_id)

            # Récupérer les informations du joueur depuis la dernière participation
            player_info = next(
                (p for d in reversed(data)
                 for p in d["participants"]
                 if p["id"] == player_id),
                None
            )

            if player_info:
                player_stats[player_id] = {
                    "name": player_info["name"],
                    "mention": player_info["mention"],
                    **stats
                }

        # Trier par taux de réussite puis par nombre total d'étoiles
        sorted_stats = sorted(
            player_stats.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["total_stars"]),
            reverse=True
        )

        return [
            {"id": player_id, **stats}
            for player_id, stats in sorted_stats
        ]