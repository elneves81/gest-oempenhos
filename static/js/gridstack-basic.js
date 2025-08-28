/**
 * GridStack Fallback Básico
 * Versão simplificada para quando os CDNs falham
 */
(function() {
    'use strict';
    
    // Simula as principais funcionalidades do GridStack
    class GridStackBasic {
        constructor(container, options = {}) {
            this.container = typeof container === 'string' ? document.querySelector(container) : container;
            this.options = {
                column: options.column || 12,
                cellHeight: options.cellHeight || 90,
                margin: options.margin || 8,
                animate: options.animate !== false,
                float: options.float !== false,
                minRow: options.minRow || 1,
                ...options
            };
            this.widgets = [];
            this.callbacks = {};
            
            this.init();
        }
        
        init() {
            if (!this.container) return;
            
            // Aplica estilos básicos
            this.container.style.cssText = `
                display: flex;
                flex-wrap: wrap;
                gap: ${this.options.margin}px;
                min-height: ${this.options.minRow * this.options.cellHeight}px;
                padding: ${this.options.margin}px;
            `;
            
            // Adiciona classe para identificação
            this.container.classList.add('gridstack-basic');
            
            console.log('🔧 GridStack Básico inicializado');
        }
        
        addWidget(element, options = {}) {
            if (!element) return null;
            
            const widget = {
                element: element,
                w: options.w || 3,
                h: options.h || 3,
                x: options.x || 0,
                y: options.y || 0,
                autoPosition: options.autoPosition !== false
            };
            
            // Aplica estilos ao widget
            this.styleWidget(element, widget);
            
            // Adiciona ao container
            this.container.appendChild(element);
            this.widgets.push(widget);
            
            // Vincula dados ao elemento
            element.gridstackNode = widget;
            
            // Dispara evento de change
            this.trigger('change');
            
            return element;
        }
        
        styleWidget(element, widget) {
            const colWidth = (100 / this.options.column);
            const width = colWidth * widget.w;
            const height = this.options.cellHeight * widget.h;
            
            element.style.cssText = `
                display: block;
                width: calc(${width}% - ${this.options.margin}px);
                min-height: ${height}px;
                margin-bottom: ${this.options.margin}px;
                position: relative;
                ${this.options.animate ? 'transition: all 0.3s ease;' : ''}
            `;
            
            // Adiciona classe para identificação
            element.classList.add('gridstack-item-basic');
        }
        
        removeWidget(element) {
            if (!element || !element.parentNode) return;
            
            // Remove do array
            this.widgets = this.widgets.filter(w => w.element !== element);
            
            // Remove do DOM
            element.parentNode.removeChild(element);
            
            // Dispara evento de change
            this.trigger('change');
        }
        
        removeAll() {
            this.widgets.forEach(widget => {
                if (widget.element && widget.element.parentNode) {
                    widget.element.parentNode.removeChild(widget.element);
                }
            });
            this.widgets = [];
            this.trigger('change');
        }
        
        update(element, options) {
            const widget = this.widgets.find(w => w.element === element);
            if (!widget) return;
            
            // Atualiza propriedades
            Object.assign(widget, options);
            
            // Reaplica estilos
            this.styleWidget(element, widget);
            
            // Dispara evento de change
            this.trigger('change');
        }
        
        save() {
            return this.widgets.map(widget => ({
                id: widget.element.getAttribute('gs-id') || '',
                x: widget.x,
                y: widget.y,
                w: widget.w,
                h: widget.h
            }));
        }
        
        load(layout) {
            if (!Array.isArray(layout)) return;
            
            this.removeAll();
            
            layout.forEach(item => {
                const element = document.querySelector(`[gs-id="${item.id}"]`);
                if (element) {
                    this.addWidget(element, item);
                }
            });
        }
        
        enableMove(enable = true) {
            // Modo básico: apenas log
            console.log(`🔧 Move ${enable ? 'habilitado' : 'desabilitado'} (modo básico)`);
        }
        
        enableResize(enable = true) {
            // Modo básico: apenas log
            console.log(`🔧 Resize ${enable ? 'habilitado' : 'desabilitado'} (modo básico)`);
        }
        
        setStatic(isStatic = true) {
            // Modo básico: apenas log e armazena estado
            this.isStatic = isStatic;
            console.log(`🔧 Static mode ${isStatic ? 'habilitado' : 'desabilitado'} (modo básico)`);
            
            // Em modo estático, desabilita interações
            if (isStatic) {
                this.container.style.pointerEvents = 'none';
                this.container.classList.add('gs-static');
            } else {
                this.container.style.pointerEvents = 'auto';
                this.container.classList.remove('gs-static');
            }
        }
        
        compact() {
            // Modo básico: reorganiza widgets de forma simples
            console.log('🔧 Compactando layout (modo básico)');
            // Implementação básica - apenas dispara evento
            this.trigger('change');
        }
        
        on(event, callback) {
            if (!this.callbacks[event]) {
                this.callbacks[event] = [];
            }
            this.callbacks[event].push(callback);
        }
        
        trigger(event, data = null) {
            if (this.callbacks[event]) {
                this.callbacks[event].forEach(callback => callback(data));
            }
        }
    }
    
    // Simula a API original do GridStack
    window.GridStack = {
        init: function(options = {}, selector = '.grid-stack') {
            const container = typeof selector === 'string' 
                ? document.querySelector(selector) 
                : selector;
            
            return new GridStackBasic(container, options);
        },
        
        // Outras propriedades/métodos que podem ser necessários
        Utils: {
            sort: function() { /* stub */ }
        }
    };
    
    console.log('🔧 GridStack Básico carregado com sucesso!');
})();
