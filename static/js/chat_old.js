(function () {
  const cfg = window.CHAT_CONFIG || {};
  const sendForm = document.getElementById('sendForm');
  const input = document.getElementById('messageInput');
  const sessionIdEl = document.getElementById('sessionId');
  const pane = document.getElementById('messagesPane');
  const btnNewSession = document.getElementById('btnNewSession');
  const deleteButtons = document.querySelectorAll('.btnDeleteSession');

  // Enviar mensagem
  if (sendForm) {
    sendForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = (input.value || '').trim();
      const sessionId = sessionIdEl.value;
      
      // Validação mais robusta
      if (!text) {
        alert('Digite uma mensagem primeiro.');
        return;
      }
      
      if (!sessionId || sessionId === 'undefined') {
        alert('Sessão não encontrada. Crie uma nova sessão.');
        return;
      }

      // Feedback local rápido
      appendLocalMessage(text);

      try {
        const res = await fetch(cfg.sendUrl, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ message: text, session_id: sessionId })
        });
        const data = await res.json();
        if (!data.success) {
          appendAIMessage(`Erro: ${data.error || 'Falha ao enviar.'}`);
        } else {
          appendAIMessage(data.message.ai_response);
          input.value = '';
        }
      } catch (err) {
        appendAIMessage('Erro de rede ao enviar mensagem.');
      }
      scrollToBottom();
      
      // Só atualiza gráfico se houve sucesso e há sessão válida
      if (sessionId && sessionId !== 'undefined') {
        refreshChart();
      }
    });
  }

  // Nova sessão
  if (btnNewSession) {
    btnNewSession.addEventListener('click', async () => {
      try {
        const res = await fetch(cfg.newSessionUrl, { method: 'POST' });
        const data = await res.json();
        if (data.success && data.redirect_url) {
          window.location.href = data.redirect_url;
        }
      } catch (e) {}
    });
  }

  // Deletar sessão
  deleteButtons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      const sid = btn.getAttribute('data-session');
      if (!sid) return;
      if (!confirm('Excluir esta conversa?')) return;

      const url = cfg.deleteSessionBaseUrl.replace('__ID__', sid);
      try {
        const res = await fetch(url, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          window.location.reload();
        } else {
          alert(data.error || 'Não foi possível excluir.');
        }
      } catch (e) {
        alert('Erro de rede.');
      }
    });
  });

  // Helpers UI
  function appendLocalMessage(text) {
    const html = `
      <div class="mb-2">
        <div><strong>Você</strong> <small class="text-muted">${new Date().toLocaleTimeString().slice(0,5)}</small></div>
        <div class="p-2 bg-light rounded">${escapeHtml(text)}</div>
      </div>`;
    pane.insertAdjacentHTML('beforeend', html);
  }
  function appendAIMessage(text) {
    const html = `
      <div class="mb-3">
        <div><strong>Assistente</strong></div>
        <div class="p-2 border rounded">${escapeHtml(text)}</div>
      </div>`;
    pane.insertAdjacentHTML('beforeend', html);
  }
  function scrollToBottom() {
    pane.scrollTop = pane.scrollHeight;
  }
  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, c => ({
      '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'
    }[c]));
  }

  // ------------------
  // Chart: mensagens/dia
  // ------------------
  let chart;
  const ctx = document.getElementById('chartMessages');
  async function refreshChart() {
    if (!ctx) return;
    
    // Verifica se há sessão ativa antes de tentar buscar estatísticas
    const sessionId = sessionIdEl?.value;
    if (!sessionId || sessionId === 'undefined') {
      console.log('Sessão não encontrada, pulando atualização do gráfico');
      return;
    }
    
    // Verifica se statsUrl está configurada
    if (!cfg.statsUrl) {
      console.log('statsUrl não configurada, pulando gráfico');
      return;
    }
    
    try {
      const res = await fetch(cfg.statsUrl);
      const data = await res.json();
      if (!data.success) return;

      const config = {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Mensagens',
            data: data.values,
            tension: 0.3,
            fill: false,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0,123,255,0.1)'
          }]
        },
        options: {
          responsive: true,
          animation: false,
          plugins: { legend: { display: true } },
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 } }
          }
        }
      };

      if (chart) {
        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.values;
        chart.update();
      } else {
        chart = new Chart(ctx, config);
      }
    } catch (e) {
      console.log('Erro ao carregar estatísticas do chat:', e);
    }
  }
  
  // Só chama refreshChart se há uma sessão válida
  if (sessionIdEl?.value && sessionIdEl.value !== 'undefined') {
    refreshChart();
  }
})();
