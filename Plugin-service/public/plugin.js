(function () {
  const config = window.AI_CHAT_CONFIG || {};
  if (!config.apiKey) {
    console.error("AI Chat: Missing config file!");
    return;
  }

  const baseUrl = config.serverUrl;

  function createButton() {
    const btn = document.createElement('div');
    btn.innerHTML = config.buttonIcon || '💬';

    btn.style.cssText = `
      position: fixed;
      bottom: 20px;
      ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'}
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: ${config.primaryColor};
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      cursor: pointer;
      z-index: 9999;
    `;

    btn.onclick = toggleChat;
    document.body.appendChild(btn);
  }

  function createIframe() {
    const iframe = document.createElement('iframe');
    iframe.id = 'ai-chat-frame';

    const params = new URLSearchParams({
      key: config.apiKey,
      serverUrl: config.serverUrl,
      apiPath: config.apiPath,
      title: config.title,
      subtitle: config.subtitle,
      welcome: config.welcomeMessage,
      color: config.primaryColor
    });

    iframe.src = `${baseUrl}/chat.html?${params.toString()}`;

    iframe.style.cssText = `
      position: fixed;
      bottom: 90px;
      ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'}
      width: ${config.width}px;
      height: ${config.height}px;
      border: none;
      border-radius: 12px;
      display: none;
      z-index: 9999;
    `;

    document.body.appendChild(iframe);
  }

  function toggleChat() {
    const iframe = document.getElementById('ai-chat-frame');
    iframe.style.display =
      iframe.style.display === 'none' ? 'block' : 'none';
  }

  window.addEventListener('message', (event) => {
    if (event.data === 'close-chat') {
      toggleChat();
    }
  });

  // AUTO INIT
  createButton();
  createIframe();
})();