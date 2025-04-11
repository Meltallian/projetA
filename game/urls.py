from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Core pages
    path('', views.index, name='index'),
    path('player/login/', views.player_login, name='player_login'),
    path('gm/login/', views.gm_login, name='gm_login'),
    path('logout/', views.player_logout, name='player_logout'),
   
    # Player routes
    path('player/dashboard/', views.player_dashboard, name='player_dashboard'),
    path('player/inquiry/submit/', views.submit_inquiry, name='submit_inquiry'),
    path('player/check-game-status/', views.check_game_status, name='check_game_status'),
   
    # Game Master routes
    path('gm/dashboard/', views.master_dashboard, name='master_dashboard'),
    path('gm/create-game/', views.create_game, name='create_game'),
    path('gm/game/<int:game_id>/manage/', views.manage_game, name='manage_game'),
   
    # Game control actions
    path('gm/game/<int:game_id>/start/', views.start_game, name='start_game'),
    path('gm/game/<int:game_id>/pause/', views.pause_game, name='pause_game'),
    path('gm/game/<int:game_id>/resume/', views.resume_game, name='resume_game'),
    path('gm/game/<int:game_id>/end/', views.end_game, name='end_game'),
   
    # Game Master actions
    path('gm/assign-character/', views.assign_character, name='assign_character'),
    path('gm/send-clue/', views.send_clue, name='send_clue'),
    path('gm/inquiry/<int:inquiry_id>/respond/', views.respond_to_inquiry, name='respond_to_inquiry'),
    path('gm/inquiry/<int:inquiry_id>/ignore/', views.ignore_inquiry, name='ignore_inquiry'),
    path('gm/create-event/', views.create_event, name='create_event'),
    path('gm/player/<int:player_id>/message/', views.message_player, name='message_player'),
    path('gm/player/<int:player_id>/remove/', views.remove_player, name='remove_player'),
   
    # Legacy routes - redirected to new patterns
    path('register/gm/', lambda request: redirect('gm_login'), name='register_game_master'),
    path('join/', lambda request: redirect('player_dashboard'), name='join_game'),
    path('create/', lambda request: redirect('create_game'), name='create_game_legacy'),
]