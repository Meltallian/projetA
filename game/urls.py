# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.player_login, name='player_login'),
    path('logout/', views.player_logout, name='player_logout'),
    path('register/gamemaster/', views.register_game_master, name='register_game_master'),
    
    path('join/', views.join_game, name='join_game'),
    path('create/', views.create_game, name='create_game'),
    path('lobby/<uuid:game_id>/', views.game_lobby, name='game_lobby'),
    path('master/<uuid:game_id>/', views.game_master_panel, name='game_master_panel'),
    path('master/dashboard/', views.master_dashboard, name='master_dashboard'),
    path('player/dashboard/', views.player_dashboard, name='player_dashboard'),
    path('master/<uuid:game_id>/register-players/', views.register_players, name='register_players'),
]