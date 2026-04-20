(function() {
    window.AIChat = {
        config: {},
        isOpen: false,

        init: function(config) {
            if (!config || !config.apiKey) {
                console.error('AIChat.init requires an apiKey.');
                return;
            }
            this.config = config;
            this.baseUrl = config.baseUrl || this.detectBaseUrl();
            this.widgetTitle = config.widgetTitle || 'AI Assistant';
            this.theme = config.theme || { primary: '#0084ff', accent: '#ffffff' };
            this.createChatButton();
            this.createIframe();
            this.setupListeners();
        },

        detectBaseUrl: function() {
            const script = document.currentScript;
            if (script && script.src) {
                return script.src.replace(/\/[^\/]*$/, '');
            }
            return window.location.origin;
        },

        createChatButton: function() {
            const btn = document.createElement('div');
            btn.id = 'ai-chat-trigger';
            btn.innerHTML = '??';
            btn.style.cssText = `
                position: fixed; bottom: 20px; right: 20px;
                width: 60px; height: 60px; border-radius: 50%;
                background: ${this.theme.primary}; color: ${this.theme.accent};
                display: flex; align-items: center; justify-content: center;
                font-size: 30px; cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 9999; transition: transform 0.2s;
            `;
            btn.onmouseover = () => (btn.style.transform = 'scale(1.05)');
            btn.onmouseout = () => (btn.style.transform = 'scale(1)');
            btn.onclick = () => this.toggleChat();
            document.body.appendChild(btn);
        },

        createIframe: function() {
            const iframe = document.createElement('iframe');
            iframe.id = 'ai-chat-iframe';
            iframe.src = `${this.baseUrl}/chat.html?key=${encodeURIComponent(this.config.apiKey)}`;
            iframe.style.cssText = `
                position: fixed; bottom: 90px; right: 20px;
                width: 380px; height: 600px; max-height: 80vh;
                border: none; border-radius: 12px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.2);
                z-index: 9999; background: transparent;
                display: none; opacity: 0; transition: opacity 0.3s ease;
            `;
            document.body.appendChild(iframe);
        },

        toggleChat: function() {
            const iframe = document.getElementById('ai-chat-iframe');
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                iframe.style.display = 'block';
                setTimeout(() => (iframe.style.opacity = '1'), 10);
            } else {
                iframe.style.opacity = '0';
                setTimeout(() => (iframe.style.display = 'none'), 300);
            }
        },

        setupListeners: function() {
            window.addEventListener('message', (event) => {
                if (event.origin !== this.baseUrl) return;
                if (event.data === 'close-chat') {
                    this.toggleChat();
                }
            });
        },
    };
})();
