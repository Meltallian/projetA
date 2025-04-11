import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for in-game communication"""
    
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.game_group_name = f'game_{self.game_id}'
        self.player_group_name = f'player_{self.player_id}'
        
        # Join game group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        # Join player-specific group
        await self.channel_layer.group_add(
            self.player_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update player status to connected
        await self.update_player_status('connected')
        
        # Send initial game state
        await self.send_game_state()
    
    async def disconnect(self, close_code):
        # Leave game group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        
        # Leave player-specific group
        await self.channel_layer.group_discard(
            self.player_group_name,
            self.channel_name
        )
        
        # Update player status to disconnected
        await self.update_player_status('disconnected')
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'inquiry':
            # Handle player inquiry
            await self.create_inquiry(data['text'])
        elif message_type == 'heartbeat':
            # Update last_active timestamp
            await self.update_last_active()
    
    @database_sync_to_async
    def update_player_status(self, status):
        """Update player connection status"""
        try:
            from .models import Player
            player = Player.objects.get(id=self.player_id)
            player.status = status
            player.save(update_fields=['status', 'last_active'])
            return True
        except Player.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_last_active(self):
        """Update player last_active timestamp"""
        try:
            from .models import Player
            player = Player.objects.get(id=self.player_id)
            player.last_active = timezone.now()
            player.save(update_fields=['last_active'])
            return True
        except Player.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_inquiry(self, text):
        """Create a new inquiry from this player"""
        try:
            from .models import Player, Inquiry
            player = Player.objects.get(id=self.player_id)
            inquiry = Inquiry.objects.create(
                player=player,
                text=text,
                status='pending',
                created_at=timezone.now()
            )
            
            # Return data for notification to GM
            return {
                'id': inquiry.id,
                'player': player.name,
                'text': inquiry.text,
                'time': inquiry.created_at.strftime('%I:%M %p')
            }
        except Player.DoesNotExist:
            return None
    
    @database_sync_to_async
    def send_game_state(self):
        """Send initial game state to client"""
        try:
            from .models import Player, PlayerClue, GameEvent, Inquiry
            player = Player.objects.select_related('game', 'character').get(id=self.player_id)
            game = player.game
            
            # Get player's clues
            clues = PlayerClue.objects.filter(player=player).order_by('-received_at')
            clue_data = [{
                'id': pc.clue.id,
                'title': pc.clue.title,
                'description': pc.clue.description,
                'time': pc.received_at.strftime('%I:%M %p')
            } for pc in clues]
            
            # Get game events
            events = GameEvent.objects.filter(game=game).order_by('-created_at')
            event_data = [{
                'id': event.id,
                'type': event.event_type,
                'title': event.title,
                'description': event.description,
                'time': event.created_at.strftime('%I:%M %p')
            } for event in events]
            
            # Get player's inquiries
            inquiries = Inquiry.objects.filter(player=player).order_by('-created_at')
            inquiry_data = [{
                'id': inquiry.id,
                'text': inquiry.text,
                'response': inquiry.response,
                'status': inquiry.get_status_display(),
                'status_key': inquiry.status,
                'time': inquiry.created_at.strftime('%I:%M %p')
            } for inquiry in inquiries]
            
            # Calculate game time (minutes:seconds since start)
            game_time = '00:00:00'
            if game.started_at:
                elapsed = timezone.now() - game.started_at
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                game_time = f'{hours:02}:{minutes:02}:{seconds:02}'
            
            # Send initial state
            return {
                'type': 'game_state',
                'game': {
                    'id': game.id,
                    'name': game.name,
                    'status': game.status,
                    'time': game_time
                },
                'player': {
                    'id': player.id,
                    'name': player.name,
                    'character': {
                        'name': player.character.name,
                        'description': player.character.description
                    } if player.character else None
                },
                'clues': clue_data,
                'events': event_data,
                'inquiries': inquiry_data
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Error loading game state: {str(e)}'
            }
    
    # Event handlers
    async def game_state(self, event):
        """Send game state to client"""
        await self.send(text_data=json.dumps(event))
    
    async def clue(self, event):
        """Send a new clue to the client"""
        await self.send(text_data=json.dumps(event))
    
    async def event(self, event):
        """Send a game event to the client"""
        await self.send(text_data=json.dumps(event))
    
    async def inquiry_response(self, event):
        """Send an inquiry response to the client"""
        await self.send(text_data=json.dumps(event))
    
    async def game_status(self, event):
        """Send game status update to the client"""
        await self.send(text_data=json.dumps(event))
    
    async def timer_update(self, event):
        """Send timer update to the client"""
        await self.send(text_data=json.dumps(event))
    
    async def direct_message(self, event):
        """Send a direct message to the client"""
        await self.send(text_data=json.dumps(event))

class WaitingRoomConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for waiting room communication"""
    
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.room_group_name = f'waiting_{self.game_id}'
        self.player_group_name = f'player_{self.player_id}'
        
        # Join waiting room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Join player-specific group
        await self.channel_layer.group_add(
            self.player_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update player status
        await self.update_player_status('connected')
        
        # Send current players list
        await self.send_player_update()
    
    async def disconnect(self, close_code):
        # Leave groups
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        await self.channel_layer.group_discard(
            self.player_group_name,
            self.channel_name
        )
        
        # Update player status
        await self.update_player_status('disconnected')
    
    @database_sync_to_async
    def update_player_status(self, status):
        """Update player connection status"""
        try:
            from .models import Player
            player = Player.objects.get(id=self.player_id)
            player.status = status
            player.save(update_fields=['status', 'last_active'])
            return True
        except Player.DoesNotExist:
            return False
    
    @database_sync_to_async
    def send_player_update(self):
        """Send updated player list to waiting room"""
        try:
            from .models import GameSession, Player
            game = GameSession.objects.get(id=self.game_id)
            players = Player.objects.filter(game=game)
            
            player_data = [{
                'id': player.id,
                'name': player.name,
                'status': player.status,
                'character': player.character.name if player.character else None
            } for player in players]
            
            return {
                'type': 'player_update',
                'players': player_data,
                'player_count': len(player_data)
            }
        except GameSession.DoesNotExist:
            return {
                'type': 'error',
                'message': 'Game not found'
            }
    
    # Event handlers
    async def player_update(self, event):
        """Send player update to client"""
        await self.send(text_data=json.dumps(event))
    
    async def character_assigned(self, event):
        """Send character assignment notification to client"""
        await self.send(text_data=json.dumps(event))
    
    async def game_started(self, event):
        """Send game started notification to client"""
        await self.send(text_data=json.dumps(event))
    
    async def gm_message(self, event):
        """Send game master message to client"""
        await self.send(text_data=json.dumps(event))

class GameMasterConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for game master communication"""
    
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.player_id = self.scope['url_route']['kwargs']['player_id']
        self.gm_group_name = f'gm_{self.game_id}'
        
        # Check if game master already has an active game
        has_active_game = await self.check_active_game()
        if has_active_game:
            await self.close(code=4000)  # Custom close code for "already has active game"
            return
        
        # Join game master group
        await self.channel_layer.group_add(
            self.gm_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update game master's current game
        await self.update_current_game()
        
        # Send initial game state
        await self.send_game_state()
    
    @database_sync_to_async
    def check_active_game(self):
        """Check if game master already has an active game"""
        try:
            from .models import PlayerProfile
            profile = PlayerProfile.objects.get(id=self.player_id)
            return profile.current_game is not None
        except PlayerProfile.DoesNotExist:
            return True  # Prevent connection if profile doesn't exist
    
    @database_sync_to_async
    def update_current_game(self):
        """Update game master's current game"""
        try:
            from .models import PlayerProfile, GameSession
            profile = PlayerProfile.objects.get(id=self.player_id)
            game = GameSession.objects.get(id=self.game_id)
            profile.current_game = game
            profile.save(update_fields=['current_game'])
            return True
        except (PlayerProfile.DoesNotExist, GameSession.DoesNotExist):
            return False
    
    async def disconnect(self, close_code):
        # Leave GM group
        await self.channel_layer.group_discard(
            self.gm_group_name,
            self.channel_name
        )
        
        # Clear current game if not already completed
        await self.clear_current_game()
    
    @database_sync_to_async
    def clear_current_game(self):
        """Clear game master's current game if game is not completed"""
        try:
            from .models import PlayerProfile, GameSession
            profile = PlayerProfile.objects.get(id=self.player_id)
            game = GameSession.objects.get(id=self.game_id)
            if game.status != 'completed':
                profile.current_game = None
                profile.save(update_fields=['current_game'])
            return True
        except (PlayerProfile.DoesNotExist, GameSession.DoesNotExist):
            return False
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'send_event':
            # Create and broadcast game event
            event_data = await self.create_game_event(
                data.get('event_type'),
                data.get('title'),
                data.get('description')
            )
            
            # Broadcast to all players
            if event_data:
                await self.channel_layer.group_send(
                    f'game_{self.game_id}',
                    {
                        'type': 'event',
                        'event': event_data
                    }
                )
        
        elif message_type == 'send_clue':
            # Send clue to specific player
            player_id = data.get('player_id')
            clue_data = await self.create_player_clue(
                player_id,
                data.get('title'),
                data.get('description')
            )
            
            # Send to specific player
            if clue_data:
                await self.channel_layer.group_send(
                    f'player_{player_id}',
                    {
                        'type': 'clue',
                        'clue': clue_data
                    }
                )
        
        elif message_type == 'respond_inquiry':
            # Respond to player inquiry
            inquiry_id = data.get('inquiry_id')
            player_id, response_data = await self.respond_to_inquiry(
                inquiry_id,
                data.get('response')
            )
            
            # Send to specific player
            if player_id and response_data:
                await self.channel_layer.group_send(
                    f'player_{player_id}',
                    {
                        'type': 'inquiry_response',
                        'inquiry': response_data
                    }
                )
    
    @database_sync_to_async
    def send_game_state(self):
        """Send initial game state to game master"""
        try:
            from .models import GameSession, PlayerProfile, Player, Character, Inquiry
            game = GameSession.objects.get(id=self.game_id)
            profile = PlayerProfile.objects.get(id=self.player_id)
            
            # Check if this profile is the game master
            if game.game_master_id != profile.id:
                return {
                    'type': 'error',
                    'message': 'You are not the game master for this game'
                }
            
            # Get players
            players = Player.objects.filter(game=game)
            player_data = [{
                'id': player.id,
                'name': player.name,
                'status': player.status,
                'character': {
                    'id': player.character.id,
                    'name': player.character.name
                } if player.character else None,
                'joined_at': player.joined_at.strftime('%I:%M %p'),
                'last_active': player.last_active.strftime('%I:%M %p')
            } for player in players]
            
            # Get available characters
            available_characters = Character.objects.filter(game=game).exclude(
                id__in=Player.objects.filter(game=game, character__isnull=False).values_list('character_id', flat=True)
            )
            character_data = [{
                'id': character.id,
                'name': character.name,
                'description': character.description
            } for character in available_characters]
            
            # Get inquiries
            inquiries = Inquiry.objects.filter(player__game=game).order_by('-created_at')
            inquiry_data = [{
                'id': inquiry.id,
                'player': inquiry.player.name,
                'text': inquiry.text,
                'response': inquiry.response,
                'status': inquiry.get_status_display(),
                'status_key': inquiry.status,
                'time': inquiry.created_at.strftime('%I:%M %p')
            } for inquiry in inquiries]
            
            # Calculate game time
            game_time = '00:00:00'
            if game.started_at:
                elapsed = timezone.now() - game.started_at
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                game_time = f'{hours:02}:{minutes:02}:{seconds:02}'
            
            return {
                'type': 'game_state',
                'game': {
                    'id': game.id,
                    'name': game.name,
                    'status': game.status,
                    'time': game_time,
                    'player_count': players.count(),
                    'max_players': game.max_players,
                    'created_at': game.created_at.strftime('%Y-%m-%d %I:%M %p'),
                    'started_at': game.started_at.strftime('%Y-%m-%d %I:%M %p') if game.started_at else None
                },
                'players': player_data,
                'available_characters': character_data,
                'inquiries': inquiry_data
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Error loading game state: {str(e)}'
            }
    
    @database_sync_to_async
    def create_game_event(self, event_type, title, description):
        """Create a new game event"""
        try:
            from .models import GameSession, PlayerProfile, GameEvent
            game = GameSession.objects.get(id=self.game_id)
            profile = PlayerProfile.objects.get(id=self.player_id)
            
            # Check if this profile is the game master
            if game.game_master_id != profile.id:
                return None
            
            event = GameEvent.objects.create(
                game=game,
                event_type=event_type,
                title=title,
                description=description,
                created_at=timezone.now()
            )
            
            return {
                'id': event.id,
                'type': event.event_type,
                'title': event.title,
                'description': event.description,
                'time': event.created_at.strftime('%I:%M %p')
            }
        except Exception:
            return None
    
    @database_sync_to_async
    def create_player_clue(self, player_id, title, description):
        """Create a new clue for a player"""
        try:
            from .models import GameSession, PlayerProfile, Player, Clue, PlayerClue
            game = GameSession.objects.get(id=self.game_id)
            profile = PlayerProfile.objects.get(id=self.player_id)
            player = Player.objects.get(id=player_id, game=game)
            
            # Check if this profile is the game master
            if game.game_master_id != profile.id:
                return None
            
            # Create clue
            clue = Clue.objects.create(
                game=game,
                title=title,
                description=description
            )
            
            # Assign to player
            player_clue = PlayerClue.objects.create(
                player=player,
                clue=clue,
                received_at=timezone.now()
            )
            
            return {
                'id': clue.id,
                'title': clue.title,
                'description': clue.description,
                'time': player_clue.received_at.strftime('%I:%M %p')
            }
        except Exception:
            return None
    
    @database_sync_to_async
    def respond_to_inquiry(self, inquiry_id, response):
        """Respond to a player inquiry"""
        try:
            from .models import GameSession, PlayerProfile, Inquiry
            game = GameSession.objects.get(id=self.game_id)
            profile = PlayerProfile.objects.get(id=self.player_id)
            
            # Check if this profile is the game master
            if game.game_master_id != profile.id:
                return None, None
            
            inquiry = Inquiry.objects.get(id=inquiry_id, player__game=game)
            inquiry.response = response
            inquiry.status = 'answered'
            inquiry.responded_at = timezone.now()
            inquiry.save()
            
            return inquiry.player_id, {
                'id': inquiry.id,
                'text': inquiry.text,
                'response': inquiry.response,
                'status': inquiry.get_status_display(),
                'status_key': inquiry.status,
                'time': inquiry.created_at.strftime('%I:%M %p')
            }
        except Exception:
            return None, None
    
    # Event handlers
    async def game_state(self, event):
        """Send game state to client"""
        await self.send(text_data=json.dumps(event))
    
    async def player_update(self, event):
        """Send player update to client"""
        await self.send(text_data=json.dumps(event))
    
    async def new_inquiry(self, event):
        """Send new inquiry notification to client"""
        await self.send(text_data=json.dumps(event))