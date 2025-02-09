from src.config.constants import REQUIRED_ROLE_ID, ADMIN_ID

def has_required_role(interaction):
    """Vérifie si l'utilisateur a le rôle requis ou est l'admin"""
    if interaction.user.id == ADMIN_ID:
        return True
    return any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles)