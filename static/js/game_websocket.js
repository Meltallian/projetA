/**
 * Game WebSocket Management
 * Handles real-time updates for the Enchanted Forest Mystery game
 */

class GameWebSocket {
    constructor(gameId, playerId) {
        this.gameId = gameId;
        this.playerId = playerId;
        this.socket = null;
        this.handlers = {
            'clue': this.handleNewClue,
            'event': this.handleNewEvent,
            'inquiry_response': this.handleInquiryResponse,
            'game_status': this.handleGameStatus,
            'timer_update': this.handleTimerUpdate,
            'player_update': this.handlePlayerUpdate,
            'character_assigned': this.handleCharacterAssigned,
            'game_started': this.handleGameStarted,
            'gm_message': this.handleGameMasterMessage
        };
        
        this.setupWebsocket();
    }
    
    setupWebsocket() {
        // Adjust protocol (ws/wss) based on current page protocol
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/game/${this.gameId}/${this.playerId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (e) => {
            console.log("WebSocket connection established");
        };
        
        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            console.log("Message received:", data);
            
            // Handle different message types
            if (data.type && this.handlers[data.type]) {
                this.handlers[data.type](data);
            }
        };
        
        this.socket.onclose = (e) => {
            console.log("WebSocket connection closed. Reconnecting...");
            // Try to reconnect after a delay
            setTimeout(() => this.setupWebsocket(), 3000);
        };
        
        this.socket.onerror = (e) => {
            console.error("WebSocket error:", e);
        };
    }
    
    // Handle a new clue
    handleNewClue(data) {
        const clueList = document.getElementById('clue-list');
        if (!clueList) return;
        
        const noCluesMsg = clueList.querySelector('.no-clues-message') || clueList.querySelector('.empty-state');
        
        if (noCluesMsg) {
            noCluesMsg.remove();
        }
        
        const clueCard = document.createElement('div');
        clueCard.className = 'clue-card new-clue';
        clueCard.innerHTML = `
            <div class="clue-header">
                <h4>${data.clue.title}</h4>
                <span class="clue-time">${data.clue.time}</span>
            </div>
            <p>${data.clue.description}</p>
        `;
        
        clueList.prepend(clueCard);
        
        // Highlight new clue briefly
        setTimeout(() => {
            clueCard.classList.remove('new-clue');
        }, 5000);
    }
    
    // Handle a new event
    handleNewEvent(data) {
        // Skip pause and resume events
        if (data.event.title === 'Game Paused' || data.event.title === 'Game Resumed') {
            return;
        }
        
        const eventList = document.getElementById('event-list');
        if (!eventList) return;
        
        const noEventsMsg = eventList.querySelector('.no-events-message') || eventList.querySelector('.empty-state');
        
        if (noEventsMsg) {
            noEventsMsg.remove();
        }
        
        const eventCard = document.createElement('div');
        eventCard.className = `event-card ${data.event.event_type} new-event`;
        eventCard.innerHTML = `
            <div class="event-header">
                <h4>${data.event.title}</h4>
                <span class="event-time">${data.event.time}</span>
            </div>
            <p>${data.event.description}</p>
        `;
        
        eventList.prepend(eventCard);
        
        // Highlight new event briefly
        setTimeout(() => {
            eventCard.classList.remove('new-event');
        }, 5000);
    }
    
    // Update an inquiry with a response
    handleInquiryResponse(data) {
        const inquiryList = document.getElementById('inquiry-list');
        if (!inquiryList) return;
        
        const inquiryCards = inquiryList.querySelectorAll('.inquiry-card');
        
        for (let card of inquiryCards) {
            // This handles both dashboard and game view format
            const questionElement = card.querySelector('.inquiry-question') || card.querySelector('.inquiry-question p');
            if (!questionElement) continue;
            
            let inquiryText;
            if (questionElement.textContent.startsWith('Q: ')) {
                inquiryText = questionElement.textContent.substring(3);
            } else if (questionElement.textContent.startsWith('Your Question: ')) {
                inquiryText = questionElement.textContent.substring(15);
            } else {
                inquiryText = questionElement.textContent;
            }
            
            if (inquiryText.trim() === data.inquiry.text.trim()) {
                const statusElement = card.querySelector('.inquiry-status');
                if (statusElement) {
                    statusElement.textContent = data.inquiry.status;
                    statusElement.className = `inquiry-status ${data.inquiry.status_key}`;
                }
                
                if (data.inquiry.response && !card.querySelector('.inquiry-response')) {
                    // Different formats for different views
                    if (card.classList.contains('dashboard-style')) {
                        const responseElem = document.createElement('div');
                        responseElem.className = 'inquiry-response';
                        responseElem.innerHTML = `
                            <p><strong>Response:</strong> ${data.inquiry.response}</p>
                            <span class="response-time">Answered: ${data.inquiry.responded_at}</span>
                        `;
                        card.appendChild(responseElem);
                    } else {
                        const responseElem = document.createElement('p');
                        responseElem.className = 'inquiry-response';
                        responseElem.textContent = `A: ${data.inquiry.response}`;
                        card.appendChild(responseElem);
                    }
                }
                
                break;
            }
        }
    }
    
    // Update game status
    handleGameStatus(data) {
        if (data.status === 'completed') {
            // Redirect to results page or show completion overlay
            window.location.href = data.redirect_url || window.location.href;
        } else if (data.status === 'paused') {
            // Show paused game notification
            this.showNotification('Game Paused', 'The game master has paused the game. Inquiries have been disabled until the game resumes.');
            
            // Update UI to show paused state
            const inquiryForm = document.querySelector('.inquiry-form');
            if (inquiryForm && !inquiryForm.querySelector('.paused-message')) {
                // Save the form HTML to restore later
                const formHTML = inquiryForm.innerHTML;
                
                // Replace with paused message
                inquiryForm.innerHTML = `
                    <div class="paused-message">
                        <p><strong>Game is paused!</strong> Submitting inquiries is disabled until the game master resumes the game.</p>
                    </div>
                `;
                
                // Store the form HTML as a data attribute
                inquiryForm.setAttribute('data-form-html', formHTML);
            }
        } else if (data.status === 'in_progress') {
            // Show resumed game notification
            this.showNotification('Game Resumed', 'The game has been resumed by the game master. You can now submit inquiries again.');
            
            // Restore the inquiry form if needed
            const inquiryForm = document.querySelector('.inquiry-form');
            if (inquiryForm && inquiryForm.querySelector('.paused-message')) {
                const savedFormHTML = inquiryForm.getAttribute('data-form-html');
                if (savedFormHTML) {
                    inquiryForm.innerHTML = savedFormHTML;
                }
            }
        }
    }
    
    // Update players in waiting room
    handlePlayerUpdate(data) {
        const playersList = document.getElementById('players-list');
        const playerCount = document.getElementById('player-count');
        
        if (playersList) {
            playersList.innerHTML = '';
            
            data.players.forEach(player => {
                const playerItem = document.createElement('li');
                playerItem.className = 'player-item';
                playerItem.textContent = player.name;
                playersList.appendChild(playerItem);
            });
        }
        
        if (playerCount) {
            playerCount.textContent = data.player_count;
        }
    }
    
    // Handle character assignment
    handleCharacterAssigned(data) {
        const characterInfoDiv = document.querySelector('.character-info') || document.querySelector('.awaiting-character');
        
        if (characterInfoDiv) {
            const characterHTML = `
                <div class="character-card">
                    <div class="character-avatar">
                        <i class="character-icon fas 
                        ${this.getCharacterIcon(data.character.name)}"></i>
                    </div>
                    <div class="character-info">
                        <h4>${data.character.name}</h4>
                        <p>${data.character.description}</p>
                    </div>
                </div>
            `;
            
            // Replace the parent element
            characterInfoDiv.parentElement.innerHTML = characterHTML;
        }
    }
    
    // Handle game started message
    handleGameStarted(data) {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        }
    }
    
    // Handle game master message
    handleGameMasterMessage(data) {
        this.showNotification('Message from Game Master', data.message);
    }
    
    // Update the game timer
    handleTimerUpdate(data) {
        const timerElement = document.getElementById('game-timer');
        if (timerElement) {
            timerElement.textContent = data.time;
        }
    }
    
    // Helper to get character icon class
    getCharacterIcon(characterName) {
        const icons = {
            'White Mage': 'fa-heartbeat',
            'Green Mage': 'fa-leaf',
            'Magenta Sorcerer': 'fa-magic',
            'Forest Fairy': 'fa-feather-alt',
            'Druid': 'fa-paw',
            'Centaur': 'fa-horse',
            'Wood Nymph': 'fa-tree',
            'Magic Merchant': 'fa-store',
            'Mysterious Wanderer': 'fa-cloud-moon',
            'Elementalist': 'fa-fire'
        };
        
        return icons[characterName] || 'fa-user';
    }
    
    // Show notification popup
    showNotification(title, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'game-notification';
        notification.innerHTML = `
            <div class="notification-header">
                <h4>${title}</h4>
                <button class="close-btn">&times;</button>
            </div>
            <p>${message}</p>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Add close button functionality
        notification.querySelector('.close-btn').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
        
        // Auto-dismiss after 8 seconds
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 8000);
    }
}

// Initialize the WebSocket connection when the script is loaded
document.addEventListener('DOMContentLoaded', function() {
    const gameId = document.getElementById('game-id')?.value;
    const playerId = document.getElementById('player-id')?.value;
    
    if (gameId && playerId) {
        window.gameSocket = new GameWebSocket(gameId, playerId);
    }
    
    // Initialize tab switching if present
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get tab to show
                const tabToShow = this.getAttribute('data-tab');
                
                // Hide all tab panes
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Show selected tab pane
                document.getElementById(tabToShow + '-tab').classList.add('active');
            });
        });
    }
    
    // Initialize refresh button if present
    const refreshButton = document.getElementById('refresh-button');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            location.reload();
        });
    }
}); 