from django.apps import AppConfig


class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'
    
    def ready(self):
        # Import here to avoid circular imports
        from game.views import ensure_default_users_exist
        
        # Create default game master
        ensure_default_users_exist()