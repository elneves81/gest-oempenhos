/**
 * Sistema de Dashboard com Drag-and-Drop
 * Permite arrastar, soltar, redimensionar e personalizar widgets
 */

class DashboardManager {
    constructor() {
        this.widgets = new Map();
        this.gridStack = null;
        this.widgetLibrary = [];
        this.userPreferences = {};
        this.isEditMode = false;
        this._charts = new Map(); // <— guarda instâncias do Chart
        
        this.init();
    }

    init() {
        this.loadWidgetLibrary();
        this.loadUserPreferences();
        this.initializeGridStack();
        this.bindEvents();
        this.loadWidgets();
    }

    loadWidgetLibrary() {
        this.widgetLibrary = [
            {
                id: 'kpi-empenhos',
                name: 'KPI Empenhos',
                description: 'Métricas principais de empenhos',
                icon: 'bi-file-earmark-text',
                category: 'kpi',
                defaultSize: { w: 3, h: 2 },
                configurable: true
            },
            {
                id: 'kpi-financeiro',
                name: 'KPI Financeiro',
                description: 'Indicadores financeiros',
                icon: 'bi-currency-dollar',
                category: 'kpi',
                defaultSize: { w: 3, h: 2 },
                configurable: true
            },
            {
                id: 'kpi-contratos',
                name: 'KPI Contratos',
                description: 'Estatísticas e status dos contratos',
                icon: 'bi-file-earmark-check',
                category: 'kpi',
                defaultSize: { w: 3, h: 3 },
                configurable: true
            },
            {
                id: 'grafico-evolucao',
                name: 'Evolução Temporal',
                description: 'Gráfico de evolução dos dados',
                icon: 'bi-graph-up',
                category: 'grafico',
                defaultSize: { w: 6, h: 4 },
                configurable: true
            },
            {
                id: 'grafico-pizza',
                name: 'Distribuição por Status',
                description: 'Gráfico de pizza com status',
                icon: 'bi-pie-chart',
                category: 'grafico',
                defaultSize: { w: 4, h: 4 },
                configurable: true
            },
            {
                id: 'tabela-top-fornecedores',
                name: 'Top Fornecedores',
                description: 'Ranking dos principais fornecedores',
                icon: 'bi-building',
                category: 'tabela',
                defaultSize: { w: 4, h: 3 },
                configurable: true
            },
            {
                id: 'alertas-sistema',
                name: 'Alertas do Sistema',
                description: 'Notificações e alertas importantes',
                icon: 'bi-bell',
                category: 'alerta',
                defaultSize: { w: 4, h: 3 },
                configurable: true
            },
            {
                id: 'acoes-rapidas',
                name: 'Ações Rápidas',
                description: 'Botões de acesso rápido',
                icon: 'bi-lightning',
                category: 'acao',
                defaultSize: { w: 4, h: 2 },
                configurable: false
            },
            {
                id: 'calendario-vencimentos',
                name: 'Calendário de Vencimentos',
                description: 'Próximos vencimentos',
                icon: 'bi-calendar',
                category: 'calendario',
                defaultSize: { w: 4, h: 4 },
                configurable: true
            }
        ];
    }

    loadUserPreferences() {
        const saved = localStorage.getItem('dashboard-preferences');
        if (saved) {
            try {
                this.userPreferences = JSON.parse(saved);
            } catch (e) {
                console.warn('Erro ao carregar preferências do usuário:', e);
                this.userPreferences = {};
            }
        }
    }

    saveUserPreferences() {
        localStorage.setItem('dashboard-preferences', JSON.stringify(this.userPreferences));
    }

    initializeGridStack() {
        // Verifica se o elemento grid existe na página
        const gridElement = document.querySelector('.grid-stack');
        if (!gridElement) {
            console.log('Grid stack element not found, skipping initialization');
            return;
        }

        // Verifica se GridStack está disponível
        if (typeof GridStack === 'undefined') {
            console.error('GridStack não encontrado. Certifique-se de incluir a biblioteca.');
            return;
        }

        // card inteiro arrastável (sem handleClass)
        this.gridStack = GridStack.init({
            cellHeight: 80,
            margin: 10,
            float: false,
            animate: true,
            acceptWidgets: true,
            removable: '.trash',
            dragIn: '.widget-library-card',
            dragInOptions: { revert: 'invalid', scroll: false, appendTo: 'body', helper: 'clone' }
        });

        // Salva layout ao mover/redimensionar
        this.gridStack.on('change', (event, items) => this.onLayoutChange(items));
        this.gridStack.on('removed', (event, items) => items.forEach(i => this.removeWidget(i.id)));

        // Re-renderiza gráficos ao terminar resize/move
        this.gridStack.on('resizestop', (e, el) => this.redrawChartsInside(el));
        this.gridStack.on('dragstop', (e, el) => this.redrawChartsInside(el));
    }

    bindEvents() {
        // Botão de modo de edição
        document.getElementById('toggle-edit-mode')?.addEventListener('click', () => {
            this.toggleEditMode();
        });

        // Botão de adicionar widget
        document.getElementById('add-widget-btn')?.addEventListener('click', () => {
            this.showWidgetLibrary();
        });

        // Botão de salvar layout
        document.getElementById('save-layout-btn')?.addEventListener('click', () => {
            this.saveLayout();
        });

        // Botão de resetar layout
        document.getElementById('reset-layout-btn')?.addEventListener('click', () => {
            this.resetLayout();
        });

        // Botão de exportar dashboard
        document.getElementById('export-dashboard-btn')?.addEventListener('click', () => {
            this.exportDashboard();
        });
    }

    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        const editBtn = document.getElementById('toggle-edit-mode');
        const dashboard = document.getElementById('dashboard-grid');
        
        if (this.isEditMode) {
            editBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Finalizar Edição';
            editBtn.classList.remove('btn-outline-primary');
            editBtn.classList.add('btn-success');
            dashboard.classList.add('edit-mode');
            this.gridStack.enable();
            this.showEditControls();
        } else {
            editBtn.innerHTML = '<i class="bi bi-pencil me-1"></i>Editar Dashboard';
            editBtn.classList.remove('btn-success');
            editBtn.classList.add('btn-outline-primary');
            dashboard.classList.remove('edit-mode');
            this.gridStack.disable();
            this.hideEditControls();
            this.saveLayout();
        }
    }

    showEditControls() {
        const controls = document.getElementById('edit-controls');
        if (controls) {
            controls.style.display = 'block';
            controls.classList.add('fade-in');
        }
    }

    hideEditControls() {
        const controls = document.getElementById('edit-controls');
        if (controls) {
            controls.style.display = 'none';
            controls.classList.remove('fade-in');
        }
    }

    showWidgetLibrary() {
        const modal = new bootstrap.Modal(document.getElementById('widget-library-modal'));
        this.populateWidgetLibrary();
        modal.show();
    }

    populateWidgetLibrary() {
        const container = document.getElementById('widget-library-container');
        if (!container) return;

        const categories = [...new Set(this.widgetLibrary.map(w => w.category))];
        
        container.innerHTML = '';
        
        categories.forEach(category => {
            const categorySection = document.createElement('div');
            categorySection.className = 'widget-category mb-4';
            
            const categoryTitle = document.createElement('h6');
            categoryTitle.className = 'text-uppercase fw-bold text-muted mb-3';
            categoryTitle.textContent = this.getCategoryName(category);
            categorySection.appendChild(categoryTitle);
            
            const widgetsGrid = document.createElement('div');
            widgetsGrid.className = 'row g-3';
            
            this.widgetLibrary
                .filter(w => w.category === category)
                .forEach(widget => {
                    const widgetCard = this.createWidgetLibraryCard(widget);
                    widgetsGrid.appendChild(widgetCard);
                });
            
            categorySection.appendChild(widgetsGrid);
            container.appendChild(categorySection);
        });
    }

    getCategoryName(category) {
        const names = {
            'kpi': 'Indicadores (KPI)',
            'grafico': 'Gráficos',
            'tabela': 'Tabelas',
            'alerta': 'Alertas',
            'acao': 'Ações',
            'calendario': 'Calendário'
        };
        return names[category] || category;
    }

    createWidgetLibraryCard(widget) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        
        col.innerHTML = `
            <div class="widget-library-card" data-widget-id="${widget.id}">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center">
                        <i class="${widget.icon} fa-2x text-primary mb-3"></i>
                        <h6 class="card-title">${widget.name}</h6>
                        <p class="card-text small text-muted">${widget.description}</p>
                        <button class="btn btn-primary btn-sm add-widget-btn" data-widget-id="${widget.id}">
                            <i class="bi bi-plus-lg me-1"></i>Adicionar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Event listener para adicionar widget
        col.querySelector('.add-widget-btn').addEventListener('click', () => {
            this.addWidget(widget.id);
            bootstrap.Modal.getInstance(document.getElementById('widget-library-modal')).hide();
        });
        
        return col;
    }

    addWidget(widgetId) {
        const widgetConfig = this.widgetLibrary.find(w => w.id === widgetId);
        if (!widgetConfig) return;

        const widgetElement = this.createWidgetElement(widgetConfig);
        
        this.gridStack.addWidget(widgetElement, {
            w: widgetConfig.defaultSize.w,
            h: widgetConfig.defaultSize.h,
            autoPosition: true
        });

        this.loadWidgetData(widgetId);
        this.showSuccessMessage(`Widget "${widgetConfig.name}" adicionado com sucesso!`);
    }

    createWidgetElement(config) {
        const widgetEl = document.createElement('div');
        widgetEl.className = 'grid-stack-item';
        widgetEl.setAttribute('data-widget-id', config.id);

        const content = document.createElement('div');
        content.className = 'grid-stack-item-content widget-container';

        // id único pra canvas do Chart.js quando houver
        const uniqueId = `${config.id}-${Date.now()}`;

        content.innerHTML = `
            <div class="widget card h-100 shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2">
                        <i class="${config.icon}"></i>
                        <strong>${config.name}</strong>
                    </div>
                    <div class="d-flex gap-1">
                        ${config.configurable ? `
                            <button class="btn btn-sm btn-outline-secondary no-drag widget-config-btn" data-widget-id="${config.id}">
                                <i class="bi bi-gear"></i>
                            </button>` : ``}
                        <button class="btn btn-sm btn-outline-danger no-drag widget-remove-btn" data-widget-id="${config.id}">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div id="widget-content-${config.id}" data-unique="${uniqueId}">
                        <div class="widget-loading text-muted d-flex align-items-center">
                            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                            Carregando dados...
                        </div>
                    </div>
                </div>
            </div>
        `;

        // eventos
        content.querySelector('.widget-config-btn')?.addEventListener('click', () => this.configureWidget(config.id));
        content.querySelector('.widget-remove-btn').addEventListener('click', () => this.removeWidget(config.id));

        widgetEl.appendChild(content);
        return widgetEl;
    }

    async loadWidgetData(widgetId) {
        const contentEl = document.getElementById(`widget-content-${widgetId}`);
        if (!contentEl) return;

        try {
            const data = await this.fetchWidgetData(widgetId);
            const html = this.renderWidgetContent(widgetId, data);
            contentEl.innerHTML = html;

            // Inicializa os gráficos para este widget
            this.initializeWidgetCharts(widgetId, data);
        } catch (error) {
            console.error(`Erro ao carregar dados do widget ${widgetId}:`, error);
            contentEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Erro ao carregar dados
                </div>
            `;
        }
    }

    async fetchWidgetData(widgetId) {
        try {
            const response = await fetch(`/relatorios/api/widget-data/${widgetId}`);
            if (!response.ok) {
                // Para widgets estáticos como 'acoes-rapidas', retorna sucesso
                if (response.status === 404 && widgetId === 'acoes-rapidas') {
                    return { success: true, message: 'Widget estático' };
                }
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.warn(`Erro ao carregar dados do widget ${widgetId}:`, error);
            // Retorna dados default para evitar quebrar o widget
            return { 
                error: true, 
                message: error.message,
                fallback: true 
            };
        }
    }

    renderWidgetContent(widgetId, data) {
        const uniqueId = document.getElementById(`widget-content-${widgetId}`)?.dataset?.unique || Date.now();

        switch (widgetId) {
            case 'kpi-empenhos': return this.renderKPIEmpenhos(data);
            case 'kpi-financeiro': return this.renderKPIFinanceiro(data);
            case 'kpi-contratos': return this.renderKPIContratos(data, uniqueId);
            case 'grafico-evolucao': return this.renderGraficoEvolucao(data, uniqueId);
            case 'grafico-pizza': return this.renderGraficoPizza(data, uniqueId);
            case 'tabela-top-fornecedores': return this.renderTabelaFornecedores(data);
            case 'alertas-sistema': return this.renderAlertas(data);
            case 'acoes-rapidas': return this.renderAcoesRapidas(data);
            case 'calendario-vencimentos': return this.renderCalendario(data);
            default: return '<div class="text-muted">Widget não implementado</div>';
        }
    }

    renderKPIEmpenhos(data) {
        return `
            <div class="row g-3 h-100">
                <div class="col-6">
                    <div class="kpi-mini-card bg-primary">
                        <div class="kpi-mini-value">${data.total || 0}</div>
                        <div class="kpi-mini-label">Total</div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="kpi-mini-card bg-success">
                        <div class="kpi-mini-value">${data.ativos || 0}</div>
                        <div class="kpi-mini-label">Ativos</div>
                    </div>
                </div>
                <div class="col-12">
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar bg-primary" style="width: ${(data.ativos / data.total * 100) || 0}%"></div>
                    </div>
                    <small class="text-muted">${((data.ativos / data.total * 100) || 0).toFixed(1)}% ativos</small>
                </div>
            </div>
        `;
    }

    renderKPIFinanceiro(data) {
        return `
            <div class="text-center h-100 d-flex flex-column justify-content-center">
                <div class="kpi-value text-success mb-2">
                    R$ ${this.formatCurrency(data.valor_total || 0)}
                </div>
                <div class="kpi-label text-muted">Valor Total Empenhado</div>
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="bi bi-arrow-up text-success"></i>
                        ${data.variacao || 0}% vs mês anterior
                    </small>
                </div>
            </div>
        `;
    }

    renderKPIContratos(data, uniqueId) {
        const total = data.total_contratos || 0;
        const ativos = data.ativos || 0;
        const vencendo = data.vencendo || 0;
        const vencidos = data.vencidos || 0;
        
        return `
            <div class="h-100">
                <div class="row g-2 h-100">
                    <div class="col-12">
                        <div class="text-center">
                            <div class="kpi-value text-primary mb-1">${total}</div>
                            <div class="kpi-label text-muted">Total de Contratos</div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="kpi-mini-card bg-success">
                            <div class="kpi-mini-value">${ativos}</div>
                            <div class="kpi-mini-label">Ativos</div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="kpi-mini-card bg-warning">
                            <div class="kpi-mini-value">${vencendo}</div>
                            <div class="kpi-mini-label">Vencendo</div>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="kpi-mini-card bg-danger">
                            <div class="kpi-mini-value">${vencidos}</div>
                            <div class="kpi-mini-label">Vencidos</div>
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="mt-2">
                            <div class="text-center">
                                <canvas id="chart-contratos-${uniqueId}" width="100" height="100"></canvas>
                            </div>
                            <div class="text-center mt-2">
                                <small class="text-muted">
                                    <strong>${data.valor_total || 'R$ 0,00'}</strong> valor total
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderGraficoEvolucao(data, uniqueId) {
        // cria um canvas para linha/área
        return `<canvas id="chart-evolucao-${uniqueId}" class="w-100" height="200"></canvas>`;
    }

    renderGraficoPizza(data, uniqueId) {
        // cria um canvas para pizza/donut
        return `<canvas id="chart-pizza-${uniqueId}" class="w-100" height="200"></canvas>`;
    }

    renderTabelaFornecedores(data) {
        if (!data.fornecedores || data.fornecedores.length === 0) {
            return '<div class="text-muted text-center">Nenhum fornecedor encontrado</div>';
        }

        let html = '<div class="table-responsive"><table class="table table-sm">';
        html += '<thead><tr><th>Fornecedor</th><th>Valor</th></tr></thead><tbody>';
        
        data.fornecedores.slice(0, 5).forEach(fornecedor => {
            html += `
                <tr>
                    <td class="text-truncate" style="max-width: 150px;">${fornecedor.nome}</td>
                    <td class="text-end">R$ ${this.formatCurrency(fornecedor.valor)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        return html;
    }

    renderAlertas(data) {
        if (!data.alertas || data.alertas.length === 0) {
            return '<div class="text-muted text-center">Nenhum alerta</div>';
        }

        let html = '<div class="alerts-container">';
        data.alertas.slice(0, 3).forEach(alerta => {
            html += `
                <div class="alert alert-${alerta.tipo} alert-sm mb-2">
                    <i class="${alerta.icone} me-2"></i>
                    <strong>${alerta.titulo}:</strong> ${alerta.mensagem}
                </div>
            `;
        });
        html += '</div>';
        return html;
    }

    renderAcoesRapidas(data) {
        const acoes = [
            { nome: 'Novo Empenho', url: '/empenhos/novo', icon: 'bi-plus-circle', color: 'primary' },
            { nome: 'Relatório Filtrado', url: '/relatorios/filtrado', icon: 'bi-funnel', color: 'info' },
            { nome: 'Exportar Excel', url: '/relatorios/exportar/excel', icon: 'bi-file-excel', color: 'success' },
            { nome: 'Dashboard Analytics', url: '/relatorios/analytics', icon: 'bi-graph-up', color: 'warning' }
        ];

        let html = '<div class="row g-2">';
        acoes.forEach(acao => {
            html += `
                <div class="col-6">
                    <a href="${acao.url}" class="btn btn-${acao.color} btn-sm w-100">
                        <i class="${acao.icon} me-1"></i>
                        <small>${acao.nome}</small>
                    </a>
                </div>
            `;
        });
        html += '</div>';
        return html;
    }

    renderCalendario(data) {
        return `
            <div class="calendar-widget">
                <div class="calendar-header text-center mb-3">
                    <h6 class="mb-0">${new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</h6>
                </div>
                <div class="calendar-events">
                    ${data.vencimentos ? data.vencimentos.map(v => `
                        <div class="calendar-event">
                            <div class="event-date">${new Date(v.data).getDate()}</div>
                            <div class="event-info">
                                <div class="event-title">${v.titulo}</div>
                                <div class="event-type text-muted">${v.tipo}</div>
                            </div>
                        </div>
                    `).join('') : '<div class="text-muted">Nenhum vencimento próximo</div>'}
                </div>
            </div>
        `;
    }

    initializeWidgetCharts(widgetId) {
        // Implementar inicialização de gráficos específicos
        if (widgetId === 'grafico-evolucao') {
            // Inicializar gráfico de evolução
        } else if (widgetId === 'grafico-pizza') {
            // Inicializar gráfico de pizza
        }
    }

    configureWidget(widgetId) {
        // Implementar modal de configuração do widget
        console.log('Configurar widget:', widgetId);
    }

    removeWidget(widgetId) {
        const widgetEl = document.querySelector(`[data-widget-id="${widgetId}"]`);
        if (widgetEl) {
            this.gridStack.removeWidget(widgetEl);
            this.showSuccessMessage('Widget removido com sucesso!');
        }
    }

    onLayoutChange(items) {
        // Salvar mudanças no layout
        if (this.isEditMode) {
            this.userPreferences.layout = items.map(item => ({
                id: item.id,
                x: item.x,
                y: item.y,
                w: item.w,
                h: item.h
            }));
        }
    }

    saveLayout() {
        this.saveUserPreferences();
        this.showSuccessMessage('Layout salvo com sucesso!');
    }

    resetLayout() {
        if (confirm('Tem certeza que deseja resetar o layout para o padrão?')) {
            this.userPreferences = {};
            this.saveUserPreferences();
            location.reload();
        }
    }

    exportDashboard() {
        // Implementar exportação do dashboard
        this.showInfoMessage('Funcionalidade de exportação será implementada em breve!');
    }

    loadWidgets() {
        // Carregar widgets salvos ou padrão
        const defaultWidgets = ['kpi-empenhos', 'kpi-financeiro', 'kpi-contratos', 'grafico-evolucao', 'alertas-sistema'];
        
        defaultWidgets.forEach(widgetId => {
            this.addWidget(widgetId);
        });
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showInfoMessage(message) {
        this.showToast(message, 'info');
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    initializeWidgetCharts(widgetId, data) {
        // acha o canvas pela assinatura que criamos no render
        const container = document.getElementById(`widget-content-${widgetId}`);
        if (!container) return;

        const uniqueId = container.dataset.unique;

        // GRAFICO LINHA/ÁREA
        const lineCanvas = document.getElementById(`chart-evolucao-${uniqueId}`);
        if (lineCanvas) {
            // destrói anterior se existir
            const prev = this._charts.get(lineCanvas.id);
            prev?.destroy();

            const labels = data?.evolucao?.labels || [];
            const valores = data?.evolucao?.values || [];

            const chart = new Chart(lineCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Evolução',
                        data: valores,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins:{ legend:{ display:true } },
                    scales: { x:{ grid:{ display:false } }, y:{ beginAtZero:true } }
                }
            });
            this._charts.set(lineCanvas.id, chart);
        }

        // GRAFICO PIZZA
        const pieCanvas = document.getElementById(`chart-pizza-${uniqueId}`);
        if (pieCanvas) {
            const prev = this._charts.get(pieCanvas.id);
            prev?.destroy();

            const labels = data?.pizza?.labels || ['A', 'B', 'C'];
            const valores = data?.pizza?.values || [30, 50, 20];

            const chart = new Chart(pieCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{ data: valores }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '55%',
                    plugins:{ legend:{ position:'bottom' } }
                }
            });
            this._charts.set(pieCanvas.id, chart);
        }

        // GRAFICO PIZZA DOS CONTRATOS
        const contractCanvas = document.getElementById(`chart-contratos-${uniqueId}`);
        if (contractCanvas) {
            // destrói anterior se existir
            const prev = this._charts.get(contractCanvas.id);
            prev?.destroy();

            const dadosGrafico = data?.dados_grafico || [];
            const labels = dadosGrafico.map(d => d.label);
            const valores = dadosGrafico.map(d => d.value);

            const chart = new Chart(contractCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: valores,
                        backgroundColor: [
                            '#28a745', // verde para ativos
                            '#ffc107', // amarelo para vencendo
                            '#dc3545'  // vermelho para vencidos
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
            this._charts.set(contractCanvas.id, chart);
        }
    }

    // re-renderiza os gráficos dentro de um item após drag/resize
    redrawChartsInside(el) {
        const canvases = el.querySelectorAll('canvas[id^="chart-"]');
        canvases.forEach(c => {
            const ch = this._charts.get(c.id);
            if (ch) ch.resize();
        });
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se GridStack está disponível
    if (typeof GridStack !== 'undefined') {
        window.dashboardManager = new DashboardManager();
    } else {
        console.error('GridStack não encontrado. Certifique-se de incluir a biblioteca.');
    }
});

// Função global para atualizar dados dos widgets
window.updateWidgetData = function(widgetId) {
    if (window.dashboardManager) {
        window.dashboardManager.loadWidgetData(widgetId);
    }
};

// Função global para atualizar todos os widgets
window.refreshAllWidgets = function() {
    if (window.dashboardManager) {
        document.querySelectorAll('[data-widget-id]').forEach(widget => {
            const widgetId = widget.getAttribute('data-widget-id');
            window.dashboardManager.loadWidgetData(widgetId);
        });
    }
};
