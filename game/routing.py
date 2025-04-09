from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Game WebSocket
    re_path(r'ws/game/(?P<game_id>\d+)/(?P<player_id>\d+)/$', consumers.GameConsumer.as_asgi()),
    
    # Waiting room WebSocket
    re_path(r'ws/waiting/(?P<game_id>\d+)/(?P<player_id>\d+)/$', consumers.WaitingRoomConsumer.as_asgi()),
    
    # Game Master WebSocket
    re_path(r'ws/gm/(?P<game_id>\d+)/(?P<profile_id>\d+)/$', consumers.GameMasterConsumer.as_asgi()),
]