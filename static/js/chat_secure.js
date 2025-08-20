(function () {
  const cfg = window.CHAT_CONFIG || {};
  const currentSessionId = (window.currentSessionId || "").trim();

  const $sendForm = document.getElementById('sendForm');
  const $msgInput = document.getElementById('messageInput');
  const $typing = document.getElementById('typingIndicator');
  const $counter = document.getElementById('messageCounter');
  const $btnNew = document.getElementById('btnNewSession');
  const $sessionList = document.getElementById('sessionList');
  const $messagesPane = document.getElementById('messagesPane');

  // -------- Util --------
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  function scrollToBottom() {
    if ($messagesPane) $messagesPane.scrollTop = $messagesPane.scrollHeight;
  }
  function showTyping() { if ($typing) $typing.style.display = ''; }
  function hideTyping() { if ($typing) $typing.style.display = 'none'; }

  function addUserMessage(text) {
    if (!$messagesPane) return;
    const wrap = document.createElement('div');
    wrap.className = 'message user-message mb-3';
    wrap.innerHTML = `
      <div class="d-flex justify-content-end">
        <div class="message-content" style="max-width: 70%;">
          <div class="bg-primary text-white p-3 rounded-3 shadow-sm">
            <div class="message-text">${escapeHtml(text)}</div>
          </div>
          <div class="message-meta text-end mt-1">
            <small class="text-muted">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</small>
          </div>
        </div>
      </div>`;
    $messagesPane.appendChild(wrap);
    scrollToBottom();
  }

  function addAIMessage(text, timeStr) {
    if (!$messagesPane) return;
    const wrap = document.createElement('div');
    wrap.className = 'message ai-message mb-3';
    wrap.innerHTML = `
      <div class="d-flex">
        <div class="avatar-container me-2">
          <div class="bg-success rounded-circle d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
            <i class="bi bi-robot text-white"></i>
          </div>
        </div>
        <div class="message-content flex-grow-1" style="max-width: 70%;">
          <div class="bg-light border p-3 rounded-3 shadow-sm">
            <div class="message-text">${escapeHtml(text)}</div>
          </div>
          <div class="message-meta mt-1">
            <small class="text-muted">${timeStr || new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</small>
          </div>
        </div>
      </div>`;
    $messagesPane.appendChild(wrap);
    scrollToBottom();
  }

  // -------- Novo: criar sessão --------
  if ($btnNew) {
    $btnNew.addEventListener('click', () => {
      if (!cfg.newSessionUrl) {
        alert('URL de nova sessão não configurada');
        return;
      }
      
      fetch(cfg.newSessionUrl, { method: 'POST', headers: {'Content-Type': 'application/json'} })
        .then(r => r.json())
        .then(data => {
          if (data.success && data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            alert('Erro ao criar sessão: ' + (data.error || 'desconhecido'));
          }
        })
        .catch(() => alert('Erro de conexão ao criar sessão.'));
    });
  }

  // -------- Enviar mensagem --------
  if ($sendForm) {
    $sendForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!currentSessionId) {
        alert('Crie uma nova conversa antes de enviar mensagens.');
        return;
      }
      if (!cfg.sendUrl) {
        alert('URL de envio não configurada');
        return;
      }
      
      const text = ($msgInput?.value || '').trim();
      if (!text) return;

      addUserMessage(text);
      $msgInput.value = '';
      updateCounter();
      showTyping();

      fetch(cfg.sendUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: text, session_id: currentSessionId })
      })
      .then(r => r.json())
      .then(data => {
        hideTyping();
        if (data && data.success && data.message) {
          addAIMessage(data.message.ai_response || 'Ok.', data.message.timestamp);
        } else {
          addAIMessage('Desculpe, ocorreu um erro ao processar sua mensagem.');
        }
      })
      .catch(() => {
        hideTyping();
        addAIMessage('Erro de conexão. Tente novamente.');
      });
    });

    // Ctrl+Enter para enviar
    if ($msgInput) {
      $msgInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
          $sendForm.requestSubmit();
        }
      });
      $msgInput.addEventListener('input', updateCounter);
      updateCounter();
    }
  }

  // -------- Deletar sessão (delegação) --------
  if ($sessionList) {
    $sessionList.addEventListener('click', (e) => {
      const btn = e.target.closest('.btnDeleteSession');
      if (!btn) return;
      e.preventDefault();
      const sid = btn.getAttribute('data-session');
      if (!sid) return;
      if (!confirm('Deletar esta conversa?')) return;
      if (!cfg.deleteSessionBaseUrl) {
        alert('URL de exclusão não configurada');
        return;
      }

      const url = cfg.deleteSessionBaseUrl.replace('__ID__', sid);
      fetch(url, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
          if (data.success) location.reload();
          else alert('Erro ao deletar: ' + (data.error || 'desconhecido'));
        })
        .catch(() => alert('Erro de conexão ao deletar sessão.'));
    });
  }

  // -------- Carregar mensagens da sessão ativa (opcional) --------
  if (currentSessionId && cfg.getMessagesBaseUrl) {
    const url = cfg.getMessagesBaseUrl.replace('__ID__', currentSessionId);
    // Não é obrigatório, mas se quiser sincronizar:
    // fetch(url).then(r => r.json()).then(...);
  }

  // -------- Chart (opcional: só roda se canvas existir) --------
  (function initChart(){
    const canvas = document.getElementById('chartMessages');
    if (!canvas || typeof Chart === 'undefined') return;

    try {
      const last14 = [...Array(14)].map((_, i) => {
        const d = new Date(); d.setDate(d.getDate() - (13 - i));
        return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
      });
      // Sem endpoint próprio? Mostra um dummy bonito
      const data = [...Array(14)].map(() => Math.floor(Math.random() * 6));

      new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: { labels: last14, datasets: [{ label: 'Msgs', data }] },
        options: { responsive: true, plugins: { legend: { display: false } }, scales:{ y:{ beginAtZero:true } } }
      });
    } catch (e) {
      console.warn('Erro ao inicializar gráfico:', e);
    }
  })();

  function updateCounter() {
    if (!$counter || !$msgInput) return;
    const len = ($msgInput.value || '').length;
    $counter.textContent = `${len}/2000`;
    
    // Adicionar classes de aviso
    $counter.classList.remove('text-warning', 'text-danger');
    if (len > 1800) {
      $counter.classList.add('text-warning');
    } else if (len > 2000) {
      $counter.classList.add('text-danger');
    }
  }

  // -------- Funcionalidades adicionais --------
  
  // Busca de mensagens
  const $searchInput = document.getElementById('searchMessages');
  if ($searchInput) {
    $searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const messages = document.querySelectorAll('.message');
      
      messages.forEach(msg => {
        const text = msg.textContent.toLowerCase();
        if (query && !text.includes(query)) {
          msg.style.display = 'none';
        } else {
          msg.style.display = 'block';
        }
      });
    });
  }

  // Limpar chat
  const $clearBtn = document.getElementById('clearChatBtn');
  if ($clearBtn) {
    $clearBtn.addEventListener('click', () => {
      if (!currentSessionId) {
        alert('Nenhuma sessão ativa para limpar');
        return;
      }
      if (confirm('Tem certeza que deseja limpar todas as mensagens desta conversa?')) {
        const messages = document.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
      }
    });
  }

  // Exportar chat
  const $exportBtn = document.getElementById('exportChatBtn');
  if ($exportBtn) {
    $exportBtn.addEventListener('click', () => {
      if (!currentSessionId) {
        alert('Nenhuma sessão ativa para exportar');
        return;
      }
      
      const messages = Array.from(document.querySelectorAll('.message')).map(msg => {
        const isUser = msg.classList.contains('user-message');
        const text = msg.querySelector('.message-text')?.textContent || '';
        const time = msg.querySelector('.message-meta small')?.textContent || '';
        
        return {
          type: isUser ? 'user' : 'ai',
          message: text,
          timestamp: time
        };
      });
      
      const chatData = {
        sessionId: currentSessionId,
        messages: messages,
        exportDate: new Date().toISOString()
      };
      
      const blob = new Blob([JSON.stringify(chatData, null, 2)], {
        type: 'application/json'
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat_export_${currentSessionId.substring(0, 8)}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  console.log('✅ Chat IA carregado:', {
    sessionId: currentSessionId || 'Nenhuma sessão ativa',
    config: Object.keys(cfg),
    elements: {
      form: !!$sendForm,
      input: !!$msgInput,
      newBtn: !!$btnNew,
      messagesPane: !!$messagesPane
    }
  });
})();
