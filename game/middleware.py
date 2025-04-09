from django.utils.deprecation import MiddlewareMixin
from .models import PlayerProfile

class PlayerProfileMiddleware(MiddlewareMixin):
    """
    Middleware to add the player profile to the request object
    so it's accessible in templates.
    """
    
    def process_request(self, request):
        profile_id = request.session.get('player_profile_id')
        if profile_id:
            try:
                request.profile = PlayerProfile.objects.get(id=profile_id)
            except PlayerProfile.DoesNotExist:
                request.profile = None
                if 'player_profile_id' in request.session:
                    del request.session['player_profile_id']
        else:
            request.profile = None