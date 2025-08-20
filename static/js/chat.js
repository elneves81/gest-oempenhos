(function () {
  // --- helpers ---
  function qs(sel) { return document.querySelector(sel); }
  function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }
  function escapeHtml(txt) { const d = document.createElement('div'); d.textContent = txt; return d.innerHTML; }
  function nowHHMM() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  function scrollToBottom() {
    const pane = qs('#chatMessages') || qs('#messagesPane');
    if (pane) pane.scrollTop = pane.scrollHeight;
  }

  // --- state/config ---
  const cfg = window.CHAT_CONFIG || {};
  let currentSessionId = (window.currentSessionId || '').trim();
  let isTyping = false;
  let messageHistory = [];
  let currentTypingTimeout = null;

  // --- DOM nodes (podem não existir dependendo do template) ---
  const form = qs('#chatForm') || qs('#sendForm');
  const input = qs('#messageInput');
  const typing = qs('#typingIndicator');
  const newSessionBtn = qs('#newSessionBtn') || qs('#btnNewSession');
  const searchInput = qs('#searchMessages');
  const clearChatBtn = qs('#clearChatBtn');
  const exportChatBtn = qs('#exportChatBtn');
  const voiceBtn = qs('#voiceBtn');
  const attachmentBtn = qs('#attachmentBtn');

  // --- storage local ---
  function saveToLocalStorage(key, data) {
    try {
      localStorage.setItem(`chat_${key}`, JSON.stringify(data));
    } catch (e) {
      console.warn('Erro ao salvar no localStorage:', e);
    }
  }

  function loadFromLocalStorage(key) {
    try {
      const data = localStorage.getItem(`chat_${key}`);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.warn('Erro ao carregar do localStorage:', e);
      return null;
    }
  }

  // --- guards de sessão ---
  function hasSession() {
    return Boolean(currentSessionId && currentSessionId !== 'undefined');
  }

  // --- UI: mensagens ---
  function addUserMessage(message) {
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (!box) return;

    const messageId = Date.now();
    const wrap = document.createElement('div');
    wrap.className = 'message user-message mb-3';
    wrap.setAttribute('data-message-id', messageId);
    wrap.innerHTML = `
      <div class="d-flex justify-content-end">
        <div class="message-content" style="max-width: 70%;">
          <div class="bg-primary text-white p-3 rounded-3 shadow-sm">
            <div class="message-text">${escapeHtml(message)}</div>
          </div>
          <div class="message-meta text-end mt-1">
            <small class="text-muted">${nowHHMM()}</small>
            <button class="btn btn-sm btn-link text-muted p-0 ms-2 copy-message" title="Copiar">
              <i class="bi bi-clipboard"></i>
            </button>
            <button class="btn btn-sm btn-link text-muted p-0 ms-1 edit-message" title="Editar">
              <i class="bi bi-pencil"></i>
            </button>
          </div>
        </div>
      </div>
    `;
    box.appendChild(wrap);
    
    // Adicionar ao histórico
    messageHistory.push({
      id: messageId,
      type: 'user',
      message: message,
      timestamp: new Date()
    });
    
    scrollToBottom();
    saveToLocalStorage('messageHistory', messageHistory);
  }

  function addAIMessage(message, timestamp, isTemporary = false) {
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (!box) return;

    const messageId = Date.now() + 1;
    const wrap = document.createElement('div');
    wrap.className = `message ai-message mb-3 ${isTemporary ? 'temporary' : ''}`;
    wrap.setAttribute('data-message-id', messageId);
    wrap.innerHTML = `
      <div class="d-flex">
        <div class="avatar-container me-2">
          <div class="bg-success rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
            <i class="bi bi-robot text-white"></i>
          </div>
        </div>
        <div class="message-content flex-grow-1" style="max-width: 70%;">
          <div class="bg-light border p-3 rounded-3 shadow-sm">
            <div class="message-text">${formatAIMessage(message)}</div>
          </div>
          <div class="message-meta mt-1">
            <small class="text-muted">${timestamp || nowHHMM()}</small>
            <button class="btn btn-sm btn-link text-muted p-0 ms-2 copy-message" title="Copiar">
              <i class="bi bi-clipboard"></i>
            </button>
            <button class="btn btn-sm btn-link text-muted p-0 ms-1 rate-message" title="Avaliar">
              <i class="bi bi-hand-thumbs-up"></i>
            </button>
            <button class="btn btn-sm btn-link text-muted p-0 ms-1 regenerate-message" title="Regenerar">
              <i class="bi bi-arrow-clockwise"></i>
            </button>
          </div>
        </div>
      </div>
    `;
    box.appendChild(wrap);
    
    if (!isTemporary) {
      messageHistory.push({
        id: messageId,
        type: 'ai',
        message: message,
        timestamp: new Date()
      });
      saveToLocalStorage('messageHistory', messageHistory);
    }
    
    scrollToBottom();
  }

  function formatAIMessage(message) {
    // Formatação para markdown simples
    let formatted = escapeHtml(message);
    
    // Links
    formatted = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="text-primary">$1</a>');
    
    // Negrito
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Itálico
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Código inline
    formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-secondary text-white px-1 rounded">$1</code>');
    
    // Quebras de linha
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
  }

  function showTyping() { 
    if (typing) {
      typing.classList.add('show');
      isTyping = true;
    }
  }
  
  function hideTyping() { 
    if (typing) {
      typing.classList.remove('show');
      isTyping = false;
    }
  }

  // --- funcionalidades avançadas ---
  function searchMessages(query) {
    const messages = qsa('.message');
    messages.forEach(msg => {
      const text = msg.textContent.toLowerCase();
      if (text.includes(query.toLowerCase())) {
        msg.style.display = 'block';
        msg.classList.add('highlight');
      } else {
        msg.style.display = query ? 'none' : 'block';
        msg.classList.remove('highlight');
      }
    });
  }

  function clearChat() {
    if (!confirm('Tem certeza que deseja limpar todas as mensagens desta conversa?')) return;
    
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (box) box.innerHTML = '';
    
    messageHistory = [];
    saveToLocalStorage('messageHistory', messageHistory);
  }

  function exportChat() {
    const chatData = {
      sessionId: currentSessionId,
      messages: messageHistory,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${currentSessionId}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function copyMessage(messageElement) {
    const text = messageElement.querySelector('.message-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
      showToast('Mensagem copiada!', 'success');
    }).catch(() => {
      showToast('Erro ao copiar mensagem', 'error');
    });
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      z-index: 9999;
      animation: slideInRight 0.3s ease;
    `;
    
    if (type === 'success') toast.style.backgroundColor = '#28a745';
    else if (type === 'error') toast.style.backgroundColor = '#dc3545';
    else toast.style.backgroundColor = '#007bff';
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease';
      setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
  }

  function simulateTyping() {
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (!box) return;

    const typingElement = document.createElement('div');
    typingElement.className = 'typing-indicator mb-3';
    typingElement.innerHTML = `
      <div class="d-flex">
        <div class="avatar-container me-2">
          <div class="bg-success rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
            <i class="bi bi-robot text-white"></i>
          </div>
        </div>
        <div class="typing-dots bg-light border p-3 rounded-3">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    `;
    
    box.appendChild(typingElement);
    scrollToBottom();
    
    return typingElement;
  }

  function removeTypingIndicator() {
    const typingElement = qs('.typing-indicator');
    if (typingElement) {
      typingElement.remove();
    }
  }

  // --- network calls ---
  function loadMessages() {
    if (!hasSession()) return;
    if (!cfg.getMessagesBaseUrl) return;
    const url = cfg.getMessagesBaseUrl.replace('__ID__', encodeURIComponent(currentSessionId));

    fetch(url)
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        if (!data.success) return;
        const box = qs('#chatMessages');
        if (!box) return;
        box.innerHTML = ''; // redesenha
        (data.messages || []).forEach(m => {
          // user
          addUserMessage(m.message);
          // ai
          if (m.response) addAIMessage(m.response, m.timestamp?.split(' ')?.[1]);
        });
      })
      .catch(err => console.error('Erro ao carregar mensagens:', err));
  }

  function sendMessage(message) {
    if (!hasSession()) {
      console.debug('Sem sessão; abortando envio.');
      return;
    }
    if (!cfg.sendUrl) {
      console.error('sendUrl não configurado.');
      return;
    }

    // Mostrar indicador de digitação
    const typingElement = simulateTyping();
    
    fetch(cfg.sendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: currentSessionId })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r))
    .then(data => {
      removeTypingIndicator();
      
      if (data.success) {
        addAIMessage(data.message.ai_response, data.message.timestamp);
        
        // Salvar estatísticas
        updateChatStats();
        
        showToast('Mensagem enviada com sucesso!', 'success');
      } else {
        addAIMessage('Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.', null, true);
        showToast('Erro ao processar mensagem', 'error');
      }
    })
    .catch(err => {
      removeTypingIndicator();
      console.error('Erro ao enviar mensagem:', err);
      addAIMessage('❌ Erro de conexão. Verifique sua internet e tente novamente.', null, true);
      showToast('Erro de conexão', 'error');
    });
  }

  function updateChatStats() {
    const stats = loadFromLocalStorage('chatStats') || {
      messagesCount: 0,
      sessionsCount: 0,
      lastActivity: null
    };
    
    stats.messagesCount++;
    stats.lastActivity = new Date().toISOString();
    
    saveToLocalStorage('chatStats', stats);
  }

  function createNewSession() {
    if (!cfg.newSessionUrl) return;
    fetch(cfg.newSessionUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        if (data.success && data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          alert('Erro ao criar nova sessão: ' + (data.error || 'desconhecido'));
        }
      })
      .catch(err => {
        console.error('Erro ao criar sessão:', err);
        alert('Erro de conexão');
      });
  }

  function deleteSession(sessionId) {
    if (!cfg.deleteSessionBaseUrl) return;
    if (!confirm('Tem certeza que deseja deletar esta conversa?')) return;

    const url = cfg.deleteSessionBaseUrl.replace('__ID__', encodeURIComponent(sessionId));
    fetch(url, { method: 'DELETE' })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(data => {
        if (data.success) location.reload();
        else alert('Erro ao deletar sessão: ' + (data.error || 'desconhecido'));
      })
      .catch(err => {
        console.error('Erro ao deletar sessão:', err);
        alert('Erro de conexão');
      });
  }

  // --- eventos ---
  if (form && input) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const msg = input.value.trim();
      if (!msg) return;
      if (!hasSession()) {
        showToast('Crie ou selecione uma conversa antes de enviar.', 'error');
        return;
      }
      addUserMessage(msg);
      input.value = '';
      sendMessage(msg);
    });

    // Auto-resize do textarea
    input.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });

    // Envio com Ctrl+Enter
    input.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Enter') {
        form.dispatchEvent(new Event('submit'));
      }
    });
  }

  if (newSessionBtn) newSessionBtn.addEventListener('click', createNewSession);

  // Busca de mensagens
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchMessages(e.target.value);
    });
  }

  // Limpar chat
  if (clearChatBtn) {
    clearChatBtn.addEventListener('click', clearChat);
  }

  // Exportar chat
  if (exportChatBtn) {
    exportChatBtn.addEventListener('click', exportChat);
  }

  // Eventos delegados para botões das mensagens
  document.addEventListener('click', (e) => {
    if (e.target.closest('.copy-message')) {
      const messageElement = e.target.closest('.message');
      copyMessage(messageElement);
    }
    
    if (e.target.closest('.edit-message')) {
      const messageElement = e.target.closest('.message');
      editMessage(messageElement);
    }
    
    if (e.target.closest('.rate-message')) {
      const messageElement = e.target.closest('.message');
      rateMessage(messageElement);
    }
    
    if (e.target.closest('.regenerate-message')) {
      const messageElement = e.target.closest('.message');
      regenerateMessage(messageElement);
    }
  });

  function editMessage(messageElement) {
    const textElement = messageElement.querySelector('.message-text');
    const currentText = textElement.textContent;
    
    const input = document.createElement('textarea');
    input.value = currentText;
    input.className = 'form-control';
    input.style.minHeight = '60px';
    
    textElement.style.display = 'none';
    textElement.parentNode.insertBefore(input, textElement);
    
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Salvar';
    saveBtn.className = 'btn btn-sm btn-success mt-2 me-2';
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancelar';
    cancelBtn.className = 'btn btn-sm btn-secondary mt-2';
    
    input.parentNode.appendChild(saveBtn);
    input.parentNode.appendChild(cancelBtn);
    
    saveBtn.onclick = () => {
      textElement.textContent = input.value;
      textElement.style.display = 'block';
      input.remove();
      saveBtn.remove();
      cancelBtn.remove();
      showToast('Mensagem editada!', 'success');
    };
    
    cancelBtn.onclick = () => {
      textElement.style.display = 'block';
      input.remove();
      saveBtn.remove();
      cancelBtn.remove();
    };
  }

  function rateMessage(messageElement) {
    const messageId = messageElement.getAttribute('data-message-id');
    showToast('Avaliação registrada!', 'success');
    // TODO: Implementar envio da avaliação para o backend
  }

  function regenerateMessage(messageElement) {
    const previousUserMessage = messageElement.previousElementSibling;
    if (previousUserMessage && previousUserMessage.classList.contains('user-message')) {
      const userText = previousUserMessage.querySelector('.message-text').textContent;
      sendMessage(userText);
      showToast('Regenerando resposta...', 'info');
    }
  }

  qsa('.delete-session-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-session-id');
      if (id) deleteSession(id);
    });
  });

  qsa('.session-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = item.getAttribute('data-session-id');
      if (id && id !== currentSessionId) {
        window.location.href = '/chat/?session_id=' + encodeURIComponent(id);
      }
    });
  });

  // --- boot ---
  document.addEventListener('DOMContentLoaded', () => {
    // Se não houve sessão, não chamamos nenhuma rota com ID (evita /chat/undefined)
    if (hasSession()) loadMessages();
    
    // Carregar histórico local
    const savedHistory = loadFromLocalStorage('messageHistory');
    if (savedHistory) {
      messageHistory = savedHistory;
    }
    
    // Configurar contador de caracteres
    if (input) {
      const counter = qs('#messageCounter');
      input.addEventListener('input', () => {
        const length = input.value.length;
        if (counter) {
          counter.textContent = `${length}/2000`;
          if (length > 1800) {
            counter.classList.add('text-warning');
          } else if (length > 2000) {
            counter.classList.add('text-danger');
          } else {
            counter.classList.remove('text-warning', 'text-danger');
          }
        }
      });
    }
    
    // Configurar sugestões de mensagem
    qsa('.suggestion-card').forEach(card => {
      card.addEventListener('click', () => {
        if (!hasSession()) {
          showToast('Crie uma nova conversa primeiro!', 'error');
          return;
        }
        
        const suggestion = card.textContent.trim();
        if (input) {
          input.value = `Me ajude com: ${suggestion}`;
          input.focus();
        }
      });
    });
    
    // Atalhos de teclado
    document.addEventListener('keydown', (e) => {
      // Ctrl + N = Nova sessão
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        if (newSessionBtn) newSessionBtn.click();
      }
      
      // Ctrl + K = Focar na busca
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        if (searchInput) searchInput.focus();
      }
      
      // Esc = Limpar busca
      if (e.key === 'Escape' && searchInput && searchInput.value) {
        searchInput.value = '';
        searchMessages('');
      }
    });
    
    // Mostrar estatísticas
    displayChatStats();
  });

  function displayChatStats() {
    const stats = loadFromLocalStorage('chatStats');
    if (stats) {
      console.log('📊 Estatísticas do Chat:', stats);
    }
  }
})();
