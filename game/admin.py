from django.contrib import admin
from .models import (
    PlayerProfile, 
    GameSession, 
    Character, 
    Player, 
    Clue, 
    PlayerClue, 
    Inquiry, 
    GameEvent
)

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_game_master', 'games_played', 'created_at']
    list_filter = ['is_game_master']
    search_fields = ['name']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'game_master', 'status', 'created_at', 'player_count']
    list_filter = ['status', 'scenario']
    search_fields = ['name']
    readonly_fields = ['created_at', 'started_at', 'ended_at']
    
    def player_count(self, obj):
        return obj.players.count()
    
    player_count.short_description = 'Players'

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'game']
    list_filter = ['game']
    search_fields = ['name', 'description']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'character', 'status', 'joined_at']
    list_filter = ['status', 'game']
    search_fields = ['name']
    raw_id_fields = ['profile', 'character']

@admin.register(Clue)
class ClueAdmin(admin.ModelAdmin):
    list_display = ['title', 'game']
    list_filter = ['game']
    search_fields = ['title', 'description']

@admin.register(PlayerClue)
class PlayerClueAdmin(admin.ModelAdmin):
    list_display = ['player', 'clue', 'received_at', 'is_read']
    list_filter = ['is_read']
    search_fields = ['player__name', 'clue__title']
    raw_id_fields = ['player', 'clue']

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['player', 'text', 'status', 'created_at', 'responded_at']
    list_filter = ['status']
    search_fields = ['text', 'response', 'player__name']
    raw_id_fields = ['player']

@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'game', 'created_at']
    list_filter = ['event_type', 'game']
    search_fields = ['title', 'description']
    raw_id_fields = ['game']