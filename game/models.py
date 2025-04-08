from django.db import models

# Create your models here.
# game/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PlayerProfile(models.Model):
    """Player profile without traditional authentication"""
    name = models.CharField(max_length=100)
    verification_code = models.CharField(max_length=4)
    games_played = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_game_master = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('name', 'verification_code')
    
    def __str__(self):
        return self.name

class GameSession(models.Model):
    """Represents a single instance of a murder mystery game."""
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    room_code = models.CharField(max_length=6, unique=True)
    game_master = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='hosted_games')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    max_players = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def start_game(self):
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def end_game(self):
        self.status = 'completed'
        self.ended_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.name} ({self.room_code})"


class Character(models.Model):
    """Represents a character role that can be assigned to players."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_murderer = models.BooleanField(default=False)
    is_victim = models.BooleanField(default=False)
    backstory = models.TextField()
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='characters')
    
    def __str__(self):
        return self.name


class Player(models.Model):
    """Represents a player in a game session."""
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='player_sessions')
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    character = models.OneToOneField(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='player')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('profile', 'game_session')
    
    def __str__(self):
        character_name = self.character.name if self.character else "Unassigned"
        return f"{self.profile.name} as {character_name}"


class Clue(models.Model):
    """Represents a clue in the murder mystery game."""
    CLUE_TYPES = [
        ('evidence', 'Physical Evidence'),
        ('testimony', 'Witness Testimony'),
        ('background', 'Background Information'),
        ('secret', 'Character Secret'),
    ]
    
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='clues')
    title = models.CharField(max_length=100)
    description = models.TextField()
    clue_type = models.CharField(max_length=20, choices=CLUE_TYPES)
    reveal_time = models.IntegerField(help_text="Minutes after game start when this clue is revealed")
    is_crucial = models.BooleanField(default=False)
    related_character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_clues')
    
    def __str__(self):
        return self.title


class PlayerClue(models.Model):
    """Tracks which clues have been revealed to which players."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='received_clues')
    clue = models.ForeignKey(Clue, on_delete=models.CASCADE, related_name='player_reveals')
    revealed_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('player', 'clue')
    
    def __str__(self):
        return f"{self.clue} revealed to {self.player}"


class Inquiry(models.Model):
    """Represents a question or action from a player during the game."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='inquiries')
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='inquiries')
    question = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False, help_text="If true, response will be visible to all players")
    
    def approve(self, response):
        self.status = 'approved'
        self.response = response
        self.responded_at = timezone.now()
        self.save()
    
    def reject(self, reason=None):
        self.status = 'rejected'
        if reason:
            self.response = reason
        self.responded_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Inquiry from {self.player}"


class GameEvent(models.Model):
    """Tracks significant events during the game."""
    EVENT_TYPES = [
        ('player_joined', 'Player Joined'),
        ('player_left', 'Player Left'),
        ('game_started', 'Game Started'),
        ('game_ended', 'Game Ended'),
        ('clue_revealed', 'Clue Revealed'),
        ('inquiry_submitted', 'Inquiry Submitted'),
        ('inquiry_answered', 'Inquiry Answered'),
    ]
    
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    related_player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    
    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"
