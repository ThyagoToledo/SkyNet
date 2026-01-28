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
        this.isDesktopApp = false;

        // Audio device settings
        this.selectedInputDevice = null;
        this.selectedOutputDevice = null;

        // DOM elements
        this.messagesContainer = document.getElementById('messages');
        this.textInput = document.getElementById('text-input');
        this.sendBtn = document.getElementById('send-btn');
        this.micBtn = document.getElementById('mic-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.inputDeviceSelect = document.getElementById('input-device');
        this.outputDeviceSelect = document.getElementById('output-device');
        this.desktopIndicator = document.getElementById('desktop-indicator');

        // Initialize
        this.init();
    }

    async init() {
        // Check if running in desktop app (PyWebView)
        this.isDesktopApp = typeof window.pywebview !== 'undefined';

        if (this.isDesktopApp) {
            this.desktopIndicator.textContent = '🖥️ Desktop Mode';
        }

        // Initialize particle system
        const container = document.getElementById('canvas-container');
        this.particleSystem = new ParticleSystem(container);

        // Initialize WebSocket
        this.wsClient = new SkynetClient();
        this.setupWebSocketHandlers();
        this.wsClient.connect();

        // Setup UI handlers
        this.setupUIHandlers();

        // Load audio devices
        await this.loadAudioDevices();

        // Load saved audio preferences
        this.loadAudioPreferences();

        // Show welcome message
        this.addMessage('Olá! Sou o Skynet, seu assistente pessoal. Como posso ajudar?', 'assistant');
    }

    async loadAudioDevices() {
        try {
            let inputDevices = [];
            let outputDevices = [];

            // Try to get devices from PyWebView API first
            if (this.isDesktopApp && window.pywebview.api) {
                try {
                    const devices = await window.pywebview.api.get_audio_devices();
                    inputDevices = devices.input || [];
                    outputDevices = devices.output || [];
                } catch (e) {
                    console.log('PyWebView API not available, using browser API');
                }
            }

            // Fallback to browser API
            if (inputDevices.length === 0 || outputDevices.length === 0) {
                // Request permission first
                try {
                    await navigator.mediaDevices.getUserMedia({ audio: true });
                } catch (e) {
                    console.log('Microphone permission denied');
                }

                const devices = await navigator.mediaDevices.enumerateDevices();

                if (inputDevices.length === 0) {
                    inputDevices = devices
                        .filter(d => d.kind === 'audioinput')
                        .map(d => ({ id: d.deviceId, name: d.label || `Microfone ${d.deviceId.slice(0, 8)}` }));
                }

                if (outputDevices.length === 0) {
                    outputDevices = devices
                        .filter(d => d.kind === 'audiooutput')
                        .map(d => ({ id: d.deviceId, name: d.label || `Alto-falante ${d.deviceId.slice(0, 8)}` }));
                }
            }

            // Populate dropdowns
            this.populateDeviceSelect(this.inputDeviceSelect, inputDevices, 'Selecione o microfone');
            this.populateDeviceSelect(this.outputDeviceSelect, outputDevices, 'Selecione o alto-falante');

        } catch (error) {
            console.error('Error loading audio devices:', error);
        }
    }

    populateDeviceSelect(select, devices, placeholder) {
        select.innerHTML = '';

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = placeholder;
        select.appendChild(defaultOption);

        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.id;
            option.textContent = device.name;
            select.appendChild(option);
        });
    }

    loadAudioPreferences() {
        const savedInput = localStorage.getItem('skynet_input_device');
        const savedOutput = localStorage.getItem('skynet_output_device');

        if (savedInput) {
            this.inputDeviceSelect.value = savedInput;
            this.selectedInputDevice = savedInput;
        }

        if (savedOutput) {
            this.outputDeviceSelect.value = savedOutput;
            this.selectedOutputDevice = savedOutput;
        }
    }

    saveAudioPreferences() {
        const inputDevice = this.inputDeviceSelect.value;
        const outputDevice = this.outputDeviceSelect.value;

        if (inputDevice) {
            localStorage.setItem('skynet_input_device', inputDevice);
            this.selectedInputDevice = inputDevice;
        }

        if (outputDevice) {
            localStorage.setItem('skynet_output_device', outputDevice);
            this.selectedOutputDevice = outputDevice;
        }

        // Notify PyWebView if available
        if (this.isDesktopApp && window.pywebview.api) {
            window.pywebview.api.set_audio_devices(inputDevice, outputDevice);
        }
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

        // Settings button
        this.settingsBtn.addEventListener('click', () => {
            this.openSettings();
        });

        // Modal handlers
        document.getElementById('modal-cancel').addEventListener('click', () => {
            this.closeSettings();
        });

        document.getElementById('modal-save').addEventListener('click', () => {
            this.saveAudioPreferences();
            this.closeSettings();
            this.addMessage('Configurações de áudio salvas!', 'assistant');
        });

        // Close modal on overlay click
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.closeSettings();
            }
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

        // Keyboard shortcut for settings (Ctrl+,)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === ',') {
                e.preventDefault();
                this.openSettings();
            }
            // Escape to close modal
            if (e.key === 'Escape' && this.settingsModal.classList.contains('active')) {
                this.closeSettings();
            }
        });
    }

    openSettings() {
        this.settingsModal.classList.add('active');
        this.loadAudioDevices(); // Refresh device list
    }

    closeSettings() {
        this.settingsModal.classList.remove('active');
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
            // Build audio constraints
            const constraints = { audio: true };

            // Use selected input device if available
            if (this.selectedInputDevice) {
                constraints.audio = { deviceId: { exact: this.selectedInputDevice } };
            }

            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia(constraints);

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
