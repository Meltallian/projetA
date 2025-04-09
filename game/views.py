from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_POST
import random
import string
import logging
import json

from .models import PlayerProfile, GameSession, Player, Character, Clue, PlayerClue, Inquiry, GameEvent

logger = logging.getLogger(__name__)

# Helper functions
def get_profile_from_session(request):
    """Get the current user profile from session"""
    profile_id = request.session.get('player_profile_id')
    if not profile_id:
        return None
    
    try:
        return PlayerProfile.objects.get(id=profile_id)
    except PlayerProfile.DoesNotExist:
        # Clear invalid session data
        if 'player_profile_id' in request.session:
            del request.session['player_profile_id']
        return None

def get_active_game():
    """Get the currently active game (if any)"""
    try:
        return GameSession.objects.filter(status__in=['waiting', 'in_progress', 'paused']).latest('created_at')
    except GameSession.DoesNotExist:
        return None

# View functions
def index(request):
    """Landing page for the murder mystery game app"""
    # Check if already logged in
    profile = get_profile_from_session(request)
    if profile:
        if profile.is_game_master:
            return redirect('master_dashboard')
        else:
            return redirect('player_dashboard')
            
    return render(request, 'game/index.html')

def player_login(request):
    """Player login with name and verification code"""
    # Already logged in?
    profile = get_profile_from_session(request)
    if profile and not profile.is_game_master:
        return redirect('player_dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        verification_code = request.POST.get('verification_code')
        
        logger.info(f"Login attempt: {name}")
        
        try:
            profile = PlayerProfile.objects.get(name=name, verification_code=verification_code, is_game_master=False)
            request.session['player_profile_id'] = profile.id
            logger.info(f"Player {name} logged in successfully")
            return redirect('player_dashboard')
                
        except PlayerProfile.DoesNotExist:
            logger.warning(f"No player profile found for {name}")
            messages.error(request, "Invalid name or verification code.")
    
    return render(request, 'game/login.html')

def gm_login(request):
    """Game Master login with name and verification code"""
    # Already logged in?
    profile = get_profile_from_session(request)
    if profile and profile.is_game_master:
        return redirect('master_dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        verification_code = request.POST.get('verification_code')
        
        logger.info(f"Game Master login attempt: {name}")
        
        try:
            profile = PlayerProfile.objects.get(name=name, verification_code=verification_code, is_game_master=True)
            request.session['player_profile_id'] = profile.id
            logger.info(f"Game Master {name} logged in successfully")
            return redirect('master_dashboard')
                
        except PlayerProfile.DoesNotExist:
            logger.warning(f"No game master profile found for {name}")
            messages.error(request, "Invalid name or verification code for Game Master.")
    
    return render(request, 'game/gm_login.html')

def player_logout(request):
    """Clear the player's session"""
    if 'player_profile_id' in request.session:
        del request.session['player_profile_id']
    return redirect('index')

def player_dashboard(request):
    """Player dashboard showing game status"""
    # Check authentication
    profile = get_profile_from_session(request)
    if not profile or profile.is_game_master:
        return redirect('player_login')
    
    # Get active game
    active_game = get_active_game()
    
    # If no active game, show waiting page
    if not active_game:
        return render(request, 'game/no_active_game.html', {
            'player': profile
        })
    
    # Check if player is part of the game
    player = None
    try:
        player = Player.objects.get(game=active_game, profile=profile)
    except Player.DoesNotExist:
        # Auto-join the game
        player = Player.objects.create(
            game=active_game,
            profile=profile,
            name=profile.name,
            status='connected'
        )
        logger.info(f"Player {profile.name} auto-joined game {active_game.id}")
    
    # If game is waiting, show waiting room
    if active_game.status == 'waiting':
        return render(request, 'game/waiting_room.html', {
            'game': active_game,
            'player': player
        })
    
    # If game is in progress or paused, show game view
    if active_game.status in ['in_progress', 'paused']:
        player_clues = PlayerClue.objects.filter(player=player).order_by('-received_at')
        game_events = GameEvent.objects.filter(game=active_game).order_by('-created_at')
        player_inquiries = Inquiry.objects.filter(player=player).order_by('-created_at')
        
        return render(request, 'game/game_view.html', {
            'game': active_game,
            'player': player,
            'player_clues': player_clues,
            'game_events': game_events,
            'player_inquiries': player_inquiries
        })
    
    # If game is completed, show results
    if active_game.status == 'completed':
        return render(request, 'game/player_dashboard.html', {
            'player': profile,
            'active_game': active_game
        })
    
    # Fallback
    return render(request, 'game/player_dashboard.html', {
        'player': profile,
        'active_game': active_game
    })

def master_dashboard(request):
    """Game Master dashboard for managing the active game"""
    # Check authentication
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    # Get active game
    active_game = get_active_game()
    
    return render(request, 'game/master_dashboard.html', {
        'profile': profile,
        'active_game': active_game
    })

def launch_game(request):
    """Create a new active game session"""
    # Check authentication
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    # Check if there's already an active game
    active_game = get_active_game()
    if active_game:
        messages.warning(request, "There is already an active game. End it before launching a new one.")
        return redirect('master_dashboard')
    
    if request.method == 'POST':
        # Create new game
        with transaction.atomic():
            game = GameSession.objects.create(
                name=request.POST.get('game_name', 'Murder Mystery'),
                game_master=profile,
                max_players=int(request.POST.get('max_players', 10)),
                scenario=request.POST.get('game_scenario', 'mansion_murder'),
                solution=request.POST.get('game_solution', ''),
                status='waiting'
            )
            
            # Create characters
            character_names = request.POST.getlist('character_name[]')
            character_descs = request.POST.getlist('character_desc[]')
            
            for i in range(len(character_names)):
                if character_names[i].strip():  # Skip empty names
                    Character.objects.create(
                        game=game,
                        name=character_names[i],
                        description=character_descs[i] if i < len(character_descs) else ''
                    )
            
            logger.info(f"Game Master {profile.name} launched new game {game.id}")
            messages.success(request, f"Game '{game.name}' has been launched!")
        
        return redirect('master_dashboard')
    
    return render(request, 'game/launch_game.html')

def manage_game(request, game_id):
    """Game management interface for game masters"""
    # Check authentication
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    # Get game
    game = get_object_or_404(GameSession, id=game_id)
    
    # Check if this game master owns this game
    if game.game_master != profile:
        return HttpResponseForbidden("You don't have permission to manage this game")
    
    # Get available characters (not assigned to any player)
    available_characters = Character.objects.filter(game=game).exclude(
        id__in=Player.objects.filter(game=game, character__isnull=False).values_list('character_id', flat=True)
    )
    
    # Get clues sent in this game
    clues = PlayerClue.objects.filter(player__game=game).order_by('-received_at')
    
    # Get inquiries from players
    inquiries = Inquiry.objects.filter(player__game=game).order_by('-created_at')
    
    # Get game events
    events = GameEvent.objects.filter(game=game).order_by('-created_at')
    
    return render(request, 'game/manage_game.html', {
        'profile': profile,
        'game': game,
        'available_characters': available_characters,
        'clues': clues,
        'inquiries': inquiries,
        'events': events
    })

@require_POST
def start_game(request, game_id):
    """Start the game"""
    # Check authentication
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    # Get game
    game = get_object_or_404(GameSession, id=game_id)
    
    # Check if this game master owns this game
    if game.game_master != profile:
        return HttpResponseForbidden("You don't have permission to manage this game")
    
    if game.status != 'waiting':
        messages.warning(request, "Game is not in waiting status and cannot be started.")
        return redirect('manage_game', game_id=game_id)
    
    # Start the game
    game.status = 'in_progress'
    game.started_at = timezone.now()
    game.save()
    
    # Create a game event
    GameEvent.objects.create(
        game=game,
        event_type='announcement',
        title='Game Started',
        description='The murder mystery has begun! Investigate carefully and solve the mystery.'
    )
    
    logger.info(f"Game {game.id} started by GM {profile.name}")
    messages.success(request, "Game started successfully!")
    
    # TODO: Send WebSocket notification to all players
    
    return redirect('manage_game', game_id=game_id)

@require_POST
def pause_game(request, game_id):
    """Pause the active game"""
    # Similar structure to start_game
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    game = get_object_or_404(GameSession, id=game_id)
    if game.game_master != profile:
        return HttpResponseForbidden("You don't have permission to manage this game")
    
    if game.status != 'in_progress':
        messages.warning(request, "Game is not in progress and cannot be paused.")
        return redirect('manage_game', game_id=game_id)
    
    game.status = 'paused'
    game.save()
    
    GameEvent.objects.create(
        game=game,
        event_type='announcement',
        title='Game Paused',
        description='The game has been temporarily paused by the Game Master.'
    )
    
    logger.info(f"Game {game.id} paused by GM {profile.name}")
    messages.success(request, "Game paused successfully!")
    
    # TODO: WebSocket notification
    
    return redirect('manage_game', game_id=game_id)

@require_POST
def resume_game(request, game_id):
    """Resume a paused game"""
    # Similar structure to start_game and pause_game
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    game = get_object_or_404(GameSession, id=game_id)
    if game.game_master != profile:
        return HttpResponseForbidden("You don't have permission to manage this game")
    
    if game.status != 'paused':
        messages.warning(request, "Game is not paused and cannot be resumed.")
        return redirect('manage_game', game_id=game_id)
    
    game.status = 'in_progress'
    game.save()
    
    GameEvent.objects.create(
        game=game,
        event_type='announcement',
        title='Game Resumed',
        description='The game has been resumed by the Game Master. Continue investigating!'
    )
    
    logger.info(f"Game {game.id} resumed by GM {profile.name}")
    messages.success(request, "Game resumed successfully!")
    
    # TODO: WebSocket notification
    
    return redirect('manage_game', game_id=game_id)

@require_POST
def end_game(request, game_id):
    """End the active game"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return redirect('gm_login')
    
    game = get_object_or_404(GameSession, id=game_id)
    if game.game_master != profile:
        return HttpResponseForbidden("You don't have permission to manage this game")
    
    if game.status == 'completed':
        messages.warning(request, "Game is already completed.")
        return redirect('master_dashboard')
    
    game.status = 'completed'
    game.ended_at = timezone.now()
    game.save()
    
    # Final game event revealing the solution
    GameEvent.objects.create(
        game=game,
        event_type='revelation',
        title='Mystery Solved!',
        description=f'The mystery has been solved! {game.solution}'
    )
    
    logger.info(f"Game {game.id} ended by GM {profile.name}")
    messages.success(request, "Game has been completed!")
    
    # TODO: WebSocket notification
    
    return redirect('master_dashboard')

@require_POST
def assign_character(request):
    """Assign a character to a player"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    player_id = request.POST.get('player_id')
    character_id = request.POST.get('character_id')
    
    if not player_id or not character_id:
        return JsonResponse({'success': False, 'error': 'Missing player_id or character_id'}, status=400)
    
    try:
        player = Player.objects.get(id=player_id)
        character = Character.objects.get(id=character_id)
        
        # Check if character is already assigned
        if Player.objects.filter(character=character).exists():
            return JsonResponse({'success': False, 'error': 'Character already assigned to another player'}, status=400)
        
        # Assign character
        player.character = character
        player.save()
        
        logger.info(f"Character {character.name} assigned to player {player.name}")
        
        # TODO: WebSocket notification
        
        return JsonResponse({'success': True})
        
    except (Player.DoesNotExist, Character.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Player or Character not found'}, status=404)

@require_POST
def send_clue(request):
    """Send a clue to a player"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    player_id = request.POST.get('player_id')
    clue_title = request.POST.get('clue_title')
    clue_description = request.POST.get('clue_description')
    
    if not all([player_id, clue_title, clue_description]):
        return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
    
    try:
        player = Player.objects.get(id=player_id)
        
        # Create clue
        clue = Clue.objects.create(
            game=player.game,
            title=clue_title,
            description=clue_description
        )
        
        # Assign to player
        player_clue = PlayerClue.objects.create(
            player=player,
            clue=clue,
            received_at=timezone.now()
        )
        
        logger.info(f"Clue '{clue_title}' sent to player {player.name}")
        
        # TODO: WebSocket notification
        
        return JsonResponse({'success': True})
        
    except Player.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)

@require_POST
def submit_inquiry(request):
    """Player submits an inquiry"""
    profile = get_profile_from_session(request)
    if not profile or profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    inquiry_text = request.POST.get('inquiry_text')
    
    if not inquiry_text:
        return JsonResponse({'success': False, 'error': 'Missing inquiry text'}, status=400)
    
    active_game = get_active_game()
    if not active_game:
        return JsonResponse({'success': False, 'error': 'No active game'}, status=400)
    
    try:
        player = Player.objects.get(game=active_game, profile=profile)
        
        # Create inquiry
        inquiry = Inquiry.objects.create(
            player=player,
            text=inquiry_text,
            status='pending',
            created_at=timezone.now()
        )
        
        logger.info(f"Player {player.name} submitted inquiry: {inquiry_text}")
        
        # TODO: WebSocket notification to game master
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'inquiry': {
                    'id': inquiry.id,
                    'text': inquiry.text,
                    'time': inquiry.created_at.strftime('%I:%M %p')
                }
            })
        else:
            messages.success(request, "Inquiry submitted successfully!")
            return redirect('player_dashboard')
        
    except Player.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Player not found'}, status=404)
        else:
            messages.error(request, "Error submitting inquiry.")
            return redirect('player_dashboard')

@require_POST
def respond_to_inquiry(request, inquiry_id):
    """Game master responds to a player inquiry"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    response_text = request.POST.get('response')
    
    if not response_text:
        return JsonResponse({'success': False, 'error': 'Missing response text'}, status=400)
    
    try:
        inquiry = Inquiry.objects.get(id=inquiry_id)
        
        # Update inquiry
        inquiry.response = response_text
        inquiry.status = 'answered'
        inquiry.responded_at = timezone.now()
        inquiry.save()
        
        logger.info(f"GM {profile.name} responded to inquiry {inquiry_id}")
        
        # TODO: WebSocket notification to player
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, "Response sent to player!")
            return redirect('manage_game', game_id=inquiry.player.game.id)
        
    except Inquiry.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Inquiry not found'}, status=404)
        else:
            messages.error(request, "Error responding to inquiry.")
            return redirect('master_dashboard')

@require_POST
def create_event(request):
    """Game master creates a game event"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    event_type = request.POST.get('event_type')
    event_title = request.POST.get('event_title')
    event_description = request.POST.get('event_description')
    game_id = request.POST.get('game_id')
    
    if not all([event_type, event_title, event_description, game_id]):
        return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
    
    try:
        game = GameSession.objects.get(id=game_id, game_master=profile)
        
        # Create event
        event = GameEvent.objects.create(
            game=game,
            event_type=event_type,
            title=event_title,
            description=event_description,
            created_at=timezone.now()
        )
        
        logger.info(f"GM {profile.name} created event '{event_title}' in game {game_id}")
        
        # TODO: WebSocket notification to all players
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, "Event created and sent to all players!")
            return redirect('manage_game', game_id=game_id)
        
    except GameSession.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Game not found'}, status=404)
        else:
            messages.error(request, "Error creating event.")
            return redirect('master_dashboard')

def check_game_status(request):
    """AJAX endpoint to check if there's an active game"""
    profile = get_profile_from_session(request)
    if not profile:
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=403)
    
    active_game = get_active_game()
    
    return JsonResponse({
        'success': True,
        'active_game': active_game is not None,
        'redirect_url': reverse('player_dashboard') if active_game else None
    })

# Additional actions
@require_POST
def message_player(request, player_id):
    """Send a private message to a player"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    message = request.POST.get('message')
    
    if not message:
        return JsonResponse({'success': False, 'error': 'Missing message'}, status=400)
    
    try:
        player = Player.objects.get(id=player_id)
        
        # We'll implement this using WebSockets later
        # For now, just log it
        logger.info(f"GM {profile.name} sent message to player {player.name}: {message}")
        
        messages.success(request, f"Message sent to {player.name}!")
        return redirect('manage_game', game_id=player.game.id)
        
    except Player.DoesNotExist:
        messages.error(request, "Player not found.")
        return redirect('master_dashboard')

@require_POST
def remove_player(request, player_id):
    """Remove a player from the game"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        player = Player.objects.get(id=player_id)
        player_name = player.name
        game_id = player.game.id
        
        # Remove player
        player.delete()
        
        logger.info(f"GM {profile.name} removed player {player_name} from game {game_id}")
        
        messages.success(request, f"Player {player_name} has been removed from the game.")
        return redirect('manage_game', game_id=game_id)
        
    except Player.DoesNotExist:
        messages.error(request, "Player not found.")
        return redirect('master_dashboard')

@require_POST
def ignore_inquiry(request, inquiry_id):
    """Mark an inquiry as ignored"""
    profile = get_profile_from_session(request)
    if not profile or not profile.is_game_master:
        return JsonResponse({'success': False, 'error': 'Not authorized'}, status=403)
    
    try:
        inquiry = Inquiry.objects.get(id=inquiry_id)
        
        # Update inquiry
        inquiry.status = 'ignored'
        inquiry.save()
        
        logger.info(f"GM {profile.name} ignored inquiry {inquiry_id}")
        
        messages.success(request, "Inquiry marked as ignored.")
        return redirect('manage_game', game_id=inquiry.player.game.id)
        
    except Inquiry.DoesNotExist:
        messages.error(request, "Inquiry not found.")
        return redirect('master_dashboard')