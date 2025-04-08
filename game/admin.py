# game/admin.py
from django.contrib import admin
from .models import (
    GameSession, Character, Player, Clue, 
    PlayerClue, Inquiry, GameEvent, PlayerProfile
)

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_code', 'status', 'created_at', 'started_at')
    list_filter = ('status',)
    search_fields = ('name', 'room_code')

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_murderer', 'is_victim', 'game_session')
    list_filter = ('is_murderer', 'is_victim')
    search_fields = ('name',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'game_session', 'joined_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('profile__name',)

@admin.register(Clue)
class ClueAdmin(admin.ModelAdmin):
    list_display = ('title', 'clue_type', 'reveal_time', 'is_crucial', 'game_session')
    list_filter = ('clue_type', 'is_crucial')
    search_fields = ('title', 'description')

@admin.register(PlayerClue)
class PlayerClueAdmin(admin.ModelAdmin):
    list_display = ('player', 'clue', 'revealed_at', 'is_read')
    list_filter = ('is_read',)

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('player', 'status', 'submitted_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('question', 'response')

@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'game_session', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('description',)

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'verification_code', 'games_played', 'is_game_master')
    list_filter = ('is_game_master',)
    search_fields = ('name',)