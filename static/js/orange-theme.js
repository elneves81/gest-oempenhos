// Cores padrão para gráficos - Tema Laranja
const ORANGE_THEME_COLORS = {
    primary: '#ff6b35',
    secondary: '#ff8c5a',
    success: '#28a745',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#343a40',
    
    // Paleta de laranjas para gráficos
    oranges: [
        '#ff6b35',
        '#ff8c5a', 
        '#ffa76f',
        '#ffb380',
        '#ffc195',
        '#ffcfaa',
        '#ffddbe',
        '#ffebd3'
    ],
    
    // Gradientes
    gradients: {
        primary: 'linear-gradient(135deg, #ff6b35 0%, #ff8c5a 100%)',
        light: 'linear-gradient(135deg, #ffa76f 0%, #ffb380 100%)',
        dark: 'linear-gradient(135deg, #e55a2e 0%, #ff6b35 100%)'
    }
};

// Função para aplicar tema laranja aos gráficos Chart.js
function applyOrangeTheme(chartConfig) {
    if (chartConfig.data && chartConfig.data.datasets) {
        chartConfig.data.datasets.forEach((dataset, index) => {
            if (!dataset.backgroundColor) {
                dataset.backgroundColor = ORANGE_THEME_COLORS.oranges[index % ORANGE_THEME_COLORS.oranges.length];
            }
            if (!dataset.borderColor) {
                dataset.borderColor = ORANGE_THEME_COLORS.primary;
            }
        });
    }
    return chartConfig;
}

// Exportar para uso global
window.ORANGE_THEME_COLORS = ORANGE_THEME_COLORS;
window.applyOrangeTheme = applyOrangeTheme;
