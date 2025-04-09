from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
import random
import string
from django.urls import reverse
from .models import PlayerProfile, GameSession, Player, Character
from .forms import GameMasterRegistrationForm  # Import from forms.py
from django.db import models

# Placeholder models until our actual models are implemented
# Replace these import statements with the actual model imports once they're ready

# Add at the top of views.py
import logging
logger = logging.getLogger(__name__)


# class PlayerProfile:
#     pass
class GameSession:
    pass
class Player:
    pass
class Character:
    pass

def index(request):
    """Landing page for the murder mystery game app"""
    return render(request, 'game/index.html')

def player_login(request):
    """Player login with name and verification code"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        verification_code = request.POST.get('verification_code')
        
        # Add this logging line here
        logger.error(f"Login attempt: {name}/{verification_code}")
        
        try:
            # Try to find the matching profile
            profile = PlayerProfile.objects.get(name=name, verification_code=verification_code)
            
            # Store the profile ID in session
            request.session['player_profile_id'] = profile.id
            
            # Check if game master and redirect appropriately
            if profile.is_game_master:
                # Add this logging line here
                logger.error(f"Found game master profile, redirecting to dashboard")
                return redirect('master_dashboard')
            else:
                logger.error(f"Redirecting player {profile.name} to dashboard")
                return redirect('player_dashboard')
                
        except PlayerProfile.DoesNotExist:
            # No matching profile found
            logger.error(f"No profile found for {name}/{verification_code}")
            messages.error(request, "Invalid name or verification code.")
    
    # GET request or failed login
    return render(request, 'game/login.html')

def player_logout(request):
    """Clear the player's session"""
    # Placeholder implementation
    return redirect('index')

def register_game_master(request):
    """Register as a game master"""
    if request.method == 'POST':
        # Print for debugging
        print("Received POST to register_game_master")
        print(f"POST data: {request.POST}")
        
        # Check if you're using a form
        form = GameMasterRegistrationForm(request.POST) if 'GameMasterRegistrationForm' in globals() else None
        
        if form and form.is_valid():
            profile = form.save()
            request.session['player_profile_id'] = profile.id
            print(f"Created game master profile with ID: {profile.id}")
            messages.success(request, "Game Master account created successfully!")
            return redirect('master_dashboard')
        else:
            # Manual handling if not using a form
            name = request.POST.get('name')
            verification_code = request.POST.get('verification_code')
            
            if name and verification_code:
                from game.models import PlayerProfile
                profile, created = PlayerProfile.objects.get_or_create(
                    name=name,
                    verification_code=verification_code,
                    defaults={
                        'is_game_master': True,
                    }
                )
                
                request.session['player_profile_id'] = profile.id
                print(f"Created/retrieved game master profile with ID: {profile.id}")
                messages.success(request, "Game Master account created successfully!")
                
                # Add debug print for redirect
                print(f"Redirecting to master_dashboard: {reverse('master_dashboard')}")
                return redirect('master_dashboard')
    else:
        form = GameMasterRegistrationForm() if 'GameMasterRegistrationForm' in globals() else None
    
    return render(request, 'game/register_gm.html', {'form': form})

def join_game(request):
    """Handle room code entry and game joining"""
    # Placeholder implementation
    return render(request, 'game/join_game.html')

def create_game(request):
    """Create a new game session"""
    # Placeholder implementation
    return render(request, 'game/create_game.html')

def game_lobby(request, game_id):
    """Waiting room for players before the game starts"""
    # Placeholder implementation
    return render(request, 'game/lobby.html')

def game_master_panel(request, game_id):
    """Control panel for the game master"""
    # Placeholder implementation
    return render(request, 'game/master_panel.html')

def master_dashboard(request):
    """Dashboard showing all games created by this game master"""
    # Placeholder implementation
    return render(request, 'game/master_dashboard.html')

def player_dashboard(request):
    """Dashboard showing all games the player is part of"""
    # Placeholder implementation
    return render(request, 'game/player_dashboard.html')

def register_players(request, game_id):
    """Register multiple players for a game at once"""
    # Placeholder implementation
    return render(request, 'game/register_players.html')

#Obsolete
# def ensure_default_users_exist():
#     """Make sure the default game master and test players exist"""
#     from game.models import PlayerProfile
    
#     # Create the default game master if it doesn't exist
#     PlayerProfile.objects.get_or_create(
#         name="gm",
#         verification_code="1234",
#         defaults={
#             'is_game_master': True,
#             'games_played': 0,
#         }
#     )
    
#     # Create 10 test players
#     for i in range(1, 11):
#         player_name = f"p{i}"
#         code = f"{i}"  # Formats as 4-digit number with leading zeros
        
#         PlayerProfile.objects.get_or_create(
#             name=player_name,
#             verification_code=code,
#             defaults={
#                 'is_game_master': False,
#                 'games_played': 0,
#             }
#         )