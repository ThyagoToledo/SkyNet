/**
 * WebSocket Client for Skynet
 * Handles real-time communication with the Python backend
 */

class SkynetClient {
    constructor(url) {
        this.url = url || `ws://${window.location.hostname}:8000/ws`;
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;

        // Callbacks
        this.onStateChange = null;
        this.onMessage = null;
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;
    }

    connect() {
        try {
            console.log(`[WS] Connecting to ${this.url}...`);
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('[WS] Connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;

                if (this.onConnect) {
                    this.onConnect();
                }
            };

            this.ws.onclose = (event) => {
                console.log('[WS] Disconnected', event.code, event.reason);
                this.isConnected = false;

                if (this.onDisconnect) {
                    this.onDisconnect();
                }

                // Attempt reconnection
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('[WS] Error:', error);

                if (this.onError) {
                    this.onError(error);
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('[WS] Failed to parse message:', e);
                }
            };

        } catch (error) {
            console.error('[WS] Connection failed:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WS] Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);

            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('[WS] Max reconnection attempts reached');
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'state':
                if (this.onStateChange) {
                    this.onStateChange(data.state, data.data || {});
                }
                break;

            case 'message':
                if (this.onMessage) {
                    this.onMessage(data.content, data.role || 'assistant');
                }
                break;

            case 'audio_level':
                // Handle audio level visualization
                if (this.onAudioLevel) {
                    this.onAudioLevel(data.level);
                }
                break;

            case 'error':
                console.error('[WS] Server error:', data.message);
                if (this.onError) {
                    this.onError(data.message);
                }
                break;

            case 'system':
                console.log('[WS] System message:', data.message);
                break;

            default:
                console.log('[WS] Unknown message type:', data.type);
        }
    }

    send(type, data) {
        if (!this.isConnected || !this.ws) {
            console.error('[WS] Not connected');
            return false;
        }

        try {
            const message = JSON.stringify({
                type: type,
                ...data
            });
            this.ws.send(message);
            return true;
        } catch (error) {
            console.error('[WS] Failed to send message:', error);
            return false;
        }
    }

    // Send text message to assistant
    sendMessage(text) {
        return this.send('message', { content: text });
    }

    // Start listening mode
    startListening() {
        return this.send('command', { action: 'start_listening' });
    }

    // Stop listening mode
    stopListening() {
        return this.send('command', { action: 'stop_listening' });
    }

    // Change particle mode
    setParticleMode(mode) {
        return this.send('particle', { mode: mode });
    }

    // Request system info
    requestSystemInfo() {
        return this.send('command', { action: 'system_info' });
    }

    // Disconnect
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
    }
}

// Export for use in other files
window.SkynetClient = SkynetClient;
