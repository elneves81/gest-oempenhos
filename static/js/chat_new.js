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

  // --- DOM nodes (podem não existir dependendo do template) ---
  const form = qs('#chatForm') || qs('#sendForm');
  const input = qs('#messageInput');
  const typing = qs('#typingIndicator');
  const newSessionBtn = qs('#newSessionBtn') || qs('#btnNewSession');

  // --- guards de sessão ---
  function hasSession() {
    return Boolean(currentSessionId && currentSessionId !== 'undefined');
  }

  // --- UI: mensagens ---
  function addUserMessage(message) {
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (!box) return;

    const wrap = document.createElement('div');
    wrap.className = 'message user';
    wrap.innerHTML = `
      <div class="message-bubble">${escapeHtml(message)}</div>
      <div class="message-time text-end">${nowHHMM()}</div>
    `;
    box.appendChild(wrap);
    scrollToBottom();
  }

  function addAIMessage(message, timestamp) {
    const box = qs('#chatMessages') || qs('#messagesPane');
    if (!box) return;

    const wrap = document.createElement('div');
    wrap.className = 'message ai';
    wrap.innerHTML = `
      <div class="message-bubble">
        <i class="bi bi-robot me-1"></i>${escapeHtml(message)}
      </div>
      <div class="message-time">${timestamp || nowHHMM()}</div>
    `;
    box.appendChild(wrap);
    scrollToBottom();
  }

  function showTyping() { if (typing) typing.classList.add('show'); }
  function hideTyping() { if (typing) typing.classList.remove('show'); }

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

    showTyping();
    fetch(cfg.sendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: currentSessionId })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r))
    .then(data => {
      hideTyping();
      if (data.success) {
        addAIMessage(data.message.ai_response, data.message.timestamp);
      } else {
        addAIMessage('Desculpe, ocorreu um erro ao processar sua mensagem.');
      }
    })
    .catch(err => {
      hideTyping();
      console.error('Erro ao enviar mensagem:', err);
      addAIMessage('Erro de conexão. Tente novamente.');
    });
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
        alert('Crie ou selecione uma conversa antes de enviar.');
        return;
      }
      addUserMessage(msg);
      input.value = '';
      sendMessage(msg);
    });
  }

  if (newSessionBtn) newSessionBtn.addEventListener('click', createNewSession);

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
  });
})();
