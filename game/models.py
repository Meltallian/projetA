from django.db import models
from django.utils import timezone

class PlayerProfile(models.Model):
    """User profile - can be either player or game master"""
    name = models.CharField(max_length=100)
    verification_code = models.CharField(max_length=10)
    is_game_master = models.BooleanField(default=False)
    games_played = models.IntegerField(default=0)
    current_game = models.OneToOneField('GameSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_game_master')
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        role = "GM" if self.is_game_master else "Player"
        return f"{role}: {self.name}"

class GameSession(models.Model):
    """A game session"""
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('in_progress', 'In Progress'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    SCENARIO_CHOICES = [
        ('enchanted_forest', 'The Enchanted Forest'),
    ]
    
    STEP_CHOICES = [
        (1, 'Step 1 - Initial Clues'),
        (2, 'Step 2 - More Clues'),
        (3, 'Step 3 - Final Clues'),
        (4, 'Epilogue - Resolution'),
    ]
    
    name = models.CharField(max_length=100)
    game_master = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE, related_name='current_game_session')
    scenario = models.CharField(max_length=50, choices=SCENARIO_CHOICES, default='enchanted_forest')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    step = models.IntegerField(choices=STEP_CHOICES, default=1)
    max_players = models.IntegerField(default=10)
    solution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def player_count(self):
        return self.players.count()
    
    @property
    def step_display(self):
        for step_id, step_name in self.STEP_CHOICES:
            if step_id == self.step:
                return step_name
        return "Unknown Step"
    
    @property
    def duration(self):
        """Return the duration of the game in minutes"""
        if not self.started_at:
            return 0
        
        end_time = self.ended_at or timezone.now()
        delta = end_time - self.started_at
        return int(delta.total_seconds() / 60)

class Character(models.Model):
    """Character in the enchanted forest mystery game"""
    game = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return f"{self.name} ({self.game.name})"

class Player(models.Model):
    """A player in a specific game session"""
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('inactive', 'Inactive'),
    ]
    
    game = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='game_players')
    character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='connected')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        character_name = self.character.name if self.character else "No character"
        return f"{self.name} as {character_name}"

class Clue(models.Model):
    """A clue in the game"""
    game = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='clues')
    title = models.CharField(max_length=100)
    description = models.TextField()
    step = models.IntegerField(choices=GameSession.STEP_CHOICES, default=1, 
                              help_text="The game step when this clue becomes available")
    
    def __str__(self):
        return self.title

class PlayerClue(models.Model):
    """A clue assigned to a specific player"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    clue = models.ForeignKey(Clue, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.clue.title} -> {self.player.name}"

class Inquiry(models.Model):
    """An inquiry from a player to the game master"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('ignored', 'Ignored'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='inquiries')
    text = models.TextField()
    response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Inquiry from {self.player.name}: {self.text[:30]}..."

class GameEvent(models.Model):
    """A game event that happens during the game"""
    EVENT_TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('event', 'Game Event'),
        ('revelation', 'Revelation'),
    ]
    
    game = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"