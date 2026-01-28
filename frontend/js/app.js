/**
 * Skynet Main Application
 * Orchestrates UI, particles, and WebSocket communication
 */

class SkynetApp {
    constructor() {
        // Initialize components
        this.particleSystem = null;
        this.wsClient = null;
        this.isListening = false;
        this.mediaRecorder = null;
        this.audioChunks = [];

        // DOM elements
        this.messagesContainer = document.getElementById('messages');
        this.textInput = document.getElementById('text-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');

        // Initialize
        this.init();
    }

    init() {
        // Initialize particle system
        const container = document.getElementById('canvas-container');
        this.particleSystem = new ParticleSystem(container);

        // Initialize WebSocket
        this.wsClient = new SkynetClient();
        this.setupWebSocketHandlers();
        this.wsClient.connect();

        // Setup UI handlers
        this.setupUIHandlers();

        // Show welcome message
        this.addMessage('Olá! Sou o Skynet, seu assistente pessoal. Como posso ajudar?', 'assistant');
    }

    setupWebSocketHandlers() {
        this.wsClient.onConnect = () => {
            this.updateStatus('Online', 'idle');
            console.log('Connected to Skynet backend');
        };

        this.wsClient.onDisconnect = () => {
            this.updateStatus('Desconectado', 'idle');
        };

        this.wsClient.onStateChange = (state, data) => {
            this.handleStateChange(state, data);
        };

        this.wsClient.onMessage = (content, role) => {
            this.addMessage(content, role);
        };

        this.wsClient.onError = (error) => {
            console.error('WebSocket error:', error);
            this.addMessage('Erro de conexão com o servidor.', 'error');
        };
    }

    setupUIHandlers() {
        // Send button
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key
        this.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Microphone button
        this.micBtn.addEventListener('click', () => {
            this.toggleListening();
        });

        // Particle mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                this.setParticleMode(mode);

                // Update active state
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    sendMessage() {
        const text = this.textInput.value.trim();
        if (!text) return;

        // Add to chat
        this.addMessage(text, 'user');

        // Send to backend
        this.wsClient.sendMessage(text);

        // Clear input
        this.textInput.value = '';

        // Show thinking state
        this.particleSystem.setState('thinking');
    }

    addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.textContent = content;

        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;

        // Trigger particle effect
        if (role === 'assistant') {
            this.particleSystem.triggerExplosion();
        }
    }

    async toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            await this.startListening();
        }
    }

    async startListening() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.sendAudioToBackend(audioBlob);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isListening = true;
            this.micBtn.classList.add('active');
            this.updateStatus('Ouvindo...', 'listening');
            this.particleSystem.setState('listening');

            // Also notify backend
            this.wsClient.startListening();

        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.addMessage('Não foi possível acessar o microfone.', 'error');
        }
    }

    stopListening() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        this.isListening = false;
        this.micBtn.classList.remove('active');
        this.updateStatus('Processando...', 'thinking');
        this.particleSystem.setState('thinking');

        // Notify backend
        this.wsClient.stopListening();
    }

    async sendAudioToBackend(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            const response = await fetch('/api/transcribe', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.text) {
                    this.addMessage(data.text, 'user');
                    this.wsClient.sendMessage(data.text);
                }
            }
        } catch (error) {
            console.error('Error sending audio:', error);
        }
    }

    handleStateChange(state, data) {
        switch (state) {
            case 'idle':
                this.updateStatus('Online', 'idle');
                this.particleSystem.setState('idle');
                this.particleSystem.setSpeaking(false);
                break;

            case 'listening':
                this.updateStatus('Ouvindo...', 'listening');
                this.particleSystem.setState('listening');

                // Handle voice activity data
                if (data) {
                    if (data.speaking !== undefined) {
                        this.particleSystem.setSpeaking(data.speaking);
                    }
                    if (data.volume !== undefined) {
                        this.particleSystem.setVolume(data.volume);
                    }
                }
                break;

            case 'thinking':
                this.updateStatus('Pensando...', 'thinking');
                this.particleSystem.setState('thinking');
                this.particleSystem.setSpeaking(false);
                break;

            case 'speaking':
                this.updateStatus('Falando...', 'speaking');
                this.particleSystem.setState('speaking');
                this.particleSystem.setSpeaking(false);
                // Update mode buttons to show current mode
                document.querySelectorAll('.mode-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.mode === data.particle_mode);
                });
                break;
        }
    }

    updateStatus(text, state) {
        this.statusText.textContent = text;
        this.statusIndicator.className = `status-indicator ${state}`;
    }

    setParticleMode(mode) {
        this.particleSystem.setMode(mode);
        this.wsClient.setParticleMode(mode);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.skynetApp = new SkynetApp();
});
