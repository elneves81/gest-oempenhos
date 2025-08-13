// Arquivo JavaScript para gerenciamento do modal de aditivos
// Reutilizável em index.html e detalhes.html

// Variável global para armazenar aditivos
let aditivosContrato = [];

// Função para abrir modal de aditivos
function abrirModalAditivos(contratoId, numeroContrato) {
    document.getElementById('contratoId').value = contratoId;
    document.getElementById('contratoNumero').textContent = numeroContrato;
    
    // Limpar formulário
    document.getElementById('formNovoAditivo').reset();
    document.getElementById('contratoId').value = contratoId;
    
    // Carregar aditivos existentes
    carregarAditivos(contratoId);
    
    // Abrir modal
    new bootstrap.Modal(document.getElementById('modalAditivos')).show();
}

// Função para carregar aditivos via AJAX
function carregarAditivos(contratoId) {
    fetch(`/contratos/${contratoId}/aditivos`, {
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            aditivosContrato = data.aditivos || [];
            renderizarListaAditivos();
            atualizarOpcoesNumero();
        })
        .catch(error => {
            console.error('Erro ao carregar aditivos:', error);
            document.getElementById('listaAditivos').innerHTML = 
                '<div class="alert alert-warning">Erro ao carregar aditivos existentes.</div>';
        });
}

// Função para renderizar lista de aditivos
function renderizarListaAditivos() {
    const container = document.getElementById('listaAditivos');
    
    if (aditivosContrato.length === 0) {
        container.innerHTML = '<p class="text-muted"><i class="bi bi-info-circle me-1"></i>Nenhum aditivo cadastrado ainda.</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    aditivosContrato.forEach(aditivo => {
        const dataFormatada = new Date(aditivo.data_aditivo).toLocaleDateString('pt-BR');
        const valor = aditivo.valor_financeiro ? 
            new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(aditivo.valor_financeiro) : 
            '';
        
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${aditivo.numero_aditivo}° Termo Aditivo</h6>
                        <p class="mb-1"><strong>Tipo:</strong> ${aditivo.tipo}</p>
                        <p class="mb-1"><strong>Data:</strong> ${dataFormatada}</p>
                        ${valor ? `<p class="mb-1"><strong>Valor:</strong> ${valor}</p>` : ''}
                        ${aditivo.prazo_dias ? `<p class="mb-1"><strong>Prazo:</strong> ${aditivo.prazo_dias} dias</p>` : ''}
                        <small>${aditivo.justificativa}</small>
                    </div>
                    <div>
                        <button class="btn btn-outline-danger btn-sm" onclick="excluirAditivo(${aditivo.id})" title="Excluir">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// Função para atualizar opções de número baseado nos existentes
function atualizarOpcoesNumero() {
    const select = document.getElementById('numeroAditivo');
    const opcoesUsadas = aditivosContrato.map(a => parseInt(a.numero_aditivo));
    
    // Encontrar próximo número disponível
    let proximoNumero = 1;
    while (opcoesUsadas.includes(proximoNumero)) {
        proximoNumero++;
    }
    
    // Sugerir próximo número
    select.value = proximoNumero.toString();
}

// Função para salvar novo aditivo
function salvarAditivo() {
    const form = document.getElementById('formNovoAditivo');
    const formData = new FormData(form);
    
    // Validação básica
    if (!formData.get('numero_aditivo') || !formData.get('tipo') || !formData.get('data_aditivo') || !formData.get('justificativa')) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }
    
    // Enviar via AJAX
    fetch('/contratos/aditivos/criar', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Recarregar aditivos
            carregarAditivos(formData.get('contrato_id'));
            
            // Limpar formulário
            form.reset();
            document.getElementById('contratoId').value = formData.get('contrato_id');
            
            // Mostrar sucesso
            alert('Aditivo criado com sucesso!');
            
            // Recarregar página se estiver na página de detalhes
            if (window.location.pathname.includes('/detalhes/')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            alert('Erro ao criar aditivo: ' + (data.error || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao salvar aditivo. Tente novamente.');
    });
}

// Função para excluir aditivo
function excluirAditivo(aditivoId) {
    if (confirm('Tem certeza que deseja excluir este aditivo?')) {
        fetch(`/contratos/aditivos/${aditivoId}/excluir`, {
            method: 'DELETE',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Recarregar aditivos
                const contratoId = document.getElementById('contratoId').value;
                carregarAditivos(contratoId);
                alert('Aditivo excluído com sucesso!');
                
                // Recarregar página se estiver na página de detalhes
                if (window.location.pathname.includes('/detalhes/')) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                alert('Erro ao excluir aditivo: ' + (data.error || 'Erro desconhecido'));
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao excluir aditivo. Tente novamente.');
        });
    }
}
