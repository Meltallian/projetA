from django.core.management.base import BaseCommand
from game.models import PlayerProfile

class Command(BaseCommand):
    help = 'Creates default game master and test players'

    def handle(self, *args, **options):
        # Create the default game master if it doesn't exist
        gm, created = PlayerProfile.objects.get_or_create(
            name="gm",
            verification_code="1234",
            defaults={
                'is_game_master': True,
                'games_played': 0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created default game master'))
        else:
            self.stdout.write('Default game master already exists')
        
        # Create 10 test players
        created_count = 0
        for i in range(1, 11):
            player_name = f"p{i}"
            code = f"{i}"
            
            player, created = PlayerProfile.objects.get_or_create(
                name=player_name,
                verification_code=code,
                defaults={
                    'is_game_master': False,
                    'games_played': 0,
                }
            )
            if created:
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new test players'))