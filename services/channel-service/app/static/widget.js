/**
 * AI Coaching Platform - Web Widget Client
 * Embeddable chat widget for websites
 */

class AIChatWidget {
    constructor(config = {}) {
        this.config = {
            apiUrl: config.apiUrl || 'ws://localhost:8004',
            widgetId: config.widgetId || 'default-widget',
            position: config.position || 'bottom-right',
            theme: config.theme || 'light',
            primaryColor: config.primaryColor || '#007bff',
            welcomeMessage: config.welcomeMessage || 'Hello! How can I help you today?',
            placeholder: config.placeholder || 'Type your message...',
            ...config
        };
        
        this.isOpen = false;
        this.websocket = null;
        this.conversationId = this.generateConversationId();
        this.messageHistory = [];
        
        this.init();
    }
    
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.createWidgetHTML();
        this.attachEventListeners();
        this.loadStyles();
        this.connectWebSocket();
    }
    
    createWidgetHTML() {
        // Widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'ai-chat-widget';
        widgetContainer.className = `ai-widget ${this.config.position} ${this.config.theme}`;
        
        widgetContainer.innerHTML = `
            <!-- Widget Toggle Button -->
            <div class="widget-toggle" id="widget-toggle">
                <div class="widget-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                    </svg>
                </div>
                <div class="widget-close-icon" style="display: none;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </div>
            </div>
            
            <!-- Widget Chat Panel -->
            <div class="widget-panel" id="widget-panel" style="display: none;">
                <div class="widget-header">
                    <h3>AI Assistant</h3>
                    <div class="connection-status" id="connection-status">
                        <span class="status-dot"></span>
                        <span class="status-text">Connecting...</span>
                    </div>
                </div>
                
                <div class="widget-messages" id="widget-messages">
                    <div class="message bot-message">
                        <div class="message-content">${this.config.welcomeMessage}</div>
                        <div class="message-time">${this.formatTime(new Date())}</div>
                    </div>
                </div>
                
                <div class="widget-input-container">
                    <div class="input-wrapper">
                        <input type="text" 
                               id="widget-input" 
                               placeholder="${this.config.placeholder}"
                               maxlength="500">
                        <button type="button" id="send-button" disabled>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="typing-indicator" id="typing-indicator" style="display: none;">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(widgetContainer);
    }
    
    attachEventListeners() {
        const toggle = document.getElementById('widget-toggle');
        const input = document.getElementById('widget-input');
        const sendButton = document.getElementById('send-button');
        
        toggle.addEventListener('click', () => this.toggleWidget());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        input.addEventListener('input', () => {
            sendButton.disabled = !input.value.trim();
        });
        
        sendButton.addEventListener('click', () => this.sendMessage());
    }
    
    toggleWidget() {
        const panel = document.getElementById('widget-panel');
        const toggle = document.getElementById('widget-toggle');
        const icon = toggle.querySelector('.widget-icon');
        const closeIcon = toggle.querySelector('.widget-close-icon');
        
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            panel.style.display = 'flex';
            icon.style.display = 'none';
            closeIcon.style.display = 'block';
            document.getElementById('widget-input').focus();
        } else {
            panel.style.display = 'none';
            icon.style.display = 'block';
            closeIcon.style.display = 'none';
        }
    }
    
    connectWebSocket() {
        try {
            const wsUrl = this.config.apiUrl.replace('http', 'ws') + '/ws/widget';
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('AI Widget: Connected to server');
                this.updateConnectionStatus('connected', 'Connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('AI Widget: Disconnected from server');
                this.updateConnectionStatus('disconnected', 'Disconnected');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('AI Widget: WebSocket error:', error);
                this.updateConnectionStatus('error', 'Connection Error');
            };
            
        } catch (error) {
            console.error('AI Widget: Failed to connect:', error);
            this.updateConnectionStatus('error', 'Connection Failed');
        }
    }
    
    updateConnectionStatus(status, text) {
        const statusElement = document.getElementById('connection-status');
        const dot = statusElement.querySelector('.status-dot');
        const textElement = statusElement.querySelector('.status-text');
        
        dot.className = `status-dot ${status}`;
        textElement.textContent = text;
    }
    
    sendMessage() {
        const input = document.getElementById('widget-input');
        const message = input.value.trim();
        
        if (!message || !this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        // Add user message to UI
        this.addMessageToUI('user', message);
        
        // Send message via WebSocket
        const payload = {
            type: 'user_message',
            content: message,
            conversation_id: this.conversationId,
            widget_id: this.config.widgetId,
            timestamp: new Date().toISOString()
        };
        
        this.websocket.send(JSON.stringify(payload));
        
        // Clear input and show typing indicator
        input.value = '';
        document.getElementById('send-button').disabled = true;
        this.showTypingIndicator();
        
        // Store message in history
        this.messageHistory.push({
            type: 'user',
            content: message,
            timestamp: new Date()
        });
    }
    
    handleIncomingMessage(data) {
        this.hideTypingIndicator();
        
        if (data.type === 'ai_response') {
            this.addMessageToUI('bot', data.content);
            this.messageHistory.push({
                type: 'bot',
                content: data.content,
                timestamp: new Date()
            });
        } else if (data.type === 'error') {
            this.addMessageToUI('system', 'Sorry, I encountered an error. Please try again.');
        }
    }
    
    addMessageToUI(type, content) {
        const messagesContainer = document.getElementById('widget-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        messageDiv.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-time">${this.formatTime(new Date())}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    showTypingIndicator() {
        document.getElementById('typing-indicator').style.display = 'flex';
    }
    
    hideTypingIndicator() {
        document.getElementById('typing-indicator').style.display = 'none';
    }
    
    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    loadStyles() {
        if (document.getElementById('ai-widget-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'ai-widget-styles';
        styles.textContent = `
            #ai-chat-widget {
                position: fixed;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            #ai-chat-widget.bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            #ai-chat-widget.bottom-left {
                bottom: 20px;
                left: 20px;
            }
            
            .widget-toggle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background-color: ${this.config.primaryColor};
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }
            
            .widget-toggle:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(0,0,0,0.3);
            }
            
            .widget-panel {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                animation: slideUp 0.3s ease;
            }
            
            @keyframes slideUp {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .widget-header {
                background: ${this.config.primaryColor};
                color: white;
                padding: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .widget-header h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            
            .connection-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #ccc;
            }
            
            .status-dot.connected { background: #4CAF50; }
            .status-dot.disconnected { background: #f44336; }
            .status-dot.error { background: #ff9800; }
            
            .widget-messages {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .message {
                max-width: 80%;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .user-message {
                align-self: flex-end;
            }
            
            .bot-message, .system-message {
                align-self: flex-start;
            }
            
            .message-content {
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .user-message .message-content {
                background: ${this.config.primaryColor};
                color: white;
            }
            
            .bot-message .message-content {
                background: #f1f3f5;
                color: #333;
            }
            
            .system-message .message-content {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            
            .message-time {
                font-size: 11px;
                color: #666;
                margin: 0 8px;
            }
            
            .widget-input-container {
                padding: 16px;
                border-top: 1px solid #e1e5e9;
            }
            
            .input-wrapper {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            #widget-input {
                flex: 1;
                border: 1px solid #ddd;
                border-radius: 20px;
                padding: 12px 16px;
                font-size: 14px;
                outline: none;
                resize: none;
            }
            
            #widget-input:focus {
                border-color: ${this.config.primaryColor};
            }
            
            #send-button {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                border: none;
                background: ${this.config.primaryColor};
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            
            #send-button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            #send-button:not(:disabled):hover {
                transform: scale(1.1);
            }
            
            .typing-indicator {
                display: flex;
                gap: 4px;
                padding: 8px 16px;
                align-items: center;
            }
            
            .typing-indicator span {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #ccc;
                animation: typing 1.4s infinite;
            }
            
            .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
            .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typing {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
            
            @media (max-width: 480px) {
                .widget-panel {
                    position: fixed;
                    bottom: 0;
                    right: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    border-radius: 0;
                }
                
                #ai-chat-widget.bottom-right,
                #ai-chat-widget.bottom-left {
                    bottom: 20px;
                    right: 20px;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }
}

// Auto-initialize if config is provided
if (typeof window !== 'undefined' && window.AIChatWidgetConfig) {
    window.aiChatWidget = new AIChatWidget(window.AIChatWidgetConfig);
}

// Export for manual initialization
window.AIChatWidget = AIChatWidget;