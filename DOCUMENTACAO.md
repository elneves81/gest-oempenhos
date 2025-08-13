# 📋 Gestão de Empenhos e Contratos

Sistema completo para gestão de empenhos orçamentários e contratos administrativos, desenvolvido em Flask com interface moderna e tema laranja.

## 🚀 Características Principais

### ✨ Interface Visual
- **Tema Laranja Moderno**: Design personalizado com cores laranja (#ff6b35) em toda a aplicação
- **Bootstrap 5**: Interface responsiva e moderna
- **Gráficos Interativos**: Charts.js com paleta de cores laranja personalizada
- **Icons Bootstrap**: Iconografia consistente em todo o sistema

### 🎯 Funcionalidades Core

#### 📊 Dashboard
- Estatísticas gerais de empenhos e contratos
- Gráficos de valores por status
- Análise temporal de empenhos
- Top 10 contratos por valor
- Cards informativos com métricas principais

#### 💼 Gestão de Empenhos
- Cadastro completo de empenhos orçamentários
- Campos: número, data, valor empenhado, valor líquido, credor, etc.
- Filtros por status (ativo, cancelado, liquidado)
- Busca avançada e ordenação
- Detalhamento completo de cada empenho

#### 📋 Gestão de Contratos
- Cadastro de contratos administrativos
- Vinculação com empenhos
- Controle de vigência e renovações
- Acompanhamento de valores contratuais
- Histórico de alterações

#### 📈 Sistema de Relatórios
- Backup automático em Excel (.xlsx)
- Fallback para CSV em caso de erro
- Exportação de dados filtrados
- Relatórios por período e status
- Importação de dados via Excel

#### 🔐 Controle de Acesso
- Sistema de login seguro
- Gestão de usuários
- Controle de sessões
- Perfis de acesso diferenciados

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask 2.3+**: Framework web principal
- **SQLAlchemy**: ORM para banco de dados
- **Flask-Login**: Gerenciamento de sessões
- **Flask-WTF**: Formulários e validação
- **Waitress**: Servidor WSGI para produção

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Chart.js**: Biblioteca de gráficos
- **Bootstrap Icons**: Iconografia
- **CSS Custom Properties**: Tema laranja personalizado

### Banco de Dados
- **SQLite**: Banco principal (desenvolvimento)
- **Suporte PostgreSQL/MySQL**: Para produção

### Exportação/Importação
- **pandas**: Manipulação de dados
- **openpyxl**: Leitura/escrita de Excel
- **CSV**: Formato de fallback

## 📁 Estrutura do Projeto

```
gestao-empenhos/
├── app.py                 # Aplicação Flask principal
├── run.py                 # Script de execução
├── models.py              # Modelos de banco de dados
├── requirements.txt       # Dependências Python
├── 
├── models/                # Modelos organizados
│   ├── empenho.py        # Modelo de Empenho
│   ├── user.py           # Modelo de Usuário
│   └── __init__.py
├── 
├── routes/                # Rotas da aplicação
│   ├── auth.py           # Autenticação
│   ├── empenhos.py       # CRUD de empenhos
│   └── relatorios.py     # Relatórios e exportação
├── 
├── templates/             # Templates Jinja2
│   ├── base.html         # Template base
│   ├── dashboard.html    # Página principal
│   ├── auth/             # Templates de autenticação
│   ├── empenhos/         # Templates de empenhos
│   ├── contratos/        # Templates de contratos
│   └── relatorios/       # Templates de relatórios
├── 
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── orange-theme.css  # Tema laranja personalizado
│   └── js/
│       └── orange-theme.js   # Utilitários JavaScript
└── 
└── utils/                 # Utilitários
    ├── export.py         # Exportação de dados
    └── import_data.py    # Importação de dados
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)
- Git

### Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/elneves81/gest-oempenhos.git
cd gest-oempenhos
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv
```

3. **Ative o ambiente virtual:**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

5. **Execute o sistema:**
```bash
python run.py
```

6. **Acesse o sistema:**
- URL: http://localhost:5000
- Login padrão: `admin`
- Senha padrão: `admin123`

## ⚙️ Configuração Avançada

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua_chave_secreta_super_segura
DATABASE_URL=sqlite:///instance/empenhos.db
FLASK_ENV=development
DEBUG=True
```

### Banco de Dados de Produção
Para PostgreSQL:
```env
DATABASE_URL=postgresql://usuario:senha@localhost/empenhos_db
```

### Servidor de Produção
Para produção, use o Waitress:
```bash
python run_debug_waitress.py
```

## 📊 Uso do Sistema

### 1. Primeiro Acesso
- Acesse com usuário `admin` e senha `admin123`
- Altere a senha padrão no perfil
- Configure usuários adicionais se necessário

### 2. Cadastro de Empenhos
- Acesse "Empenhos" no menu lateral
- Clique em "Novo Empenho"
- Preencha todos os campos obrigatórios
- Salve para finalizar o cadastro

### 3. Gestão de Contratos
- Acesse "Contratos" no menu
- Cadastre contratos e vincule aos empenhos
- Acompanhe vigências e renovações

### 4. Relatórios e Backup
- Dashboard: Visualize estatísticas gerais
- Backup: Gere arquivos Excel com todos os dados
- Filtros: Use filtros avançados para análises específicas

## 🎨 Personalização do Tema

O sistema utiliza um tema laranja personalizado através de CSS Variables:

```css
:root {
    --primary-color: #ff6b35;
    --primary-light: #ff8c42;
    --primary-dark: #e55a2b;
    --secondary-color: #ffa500;
    --accent-color: #ff7f50;
}
```

Para personalizar as cores, edite o arquivo `static/css/orange-theme.css`.

## 🔧 Manutenção

### Backup Regular
Execute backups regulares através da interface:
1. Acesse o Dashboard
2. Clique em "Backup do Sistema"
3. Faça download do arquivo Excel gerado

### Logs de Sistema
Logs são gravados automaticamente em `logs/app.log`.

### Atualizações
Para atualizar o sistema:
```bash
git pull origin main
pip install -r requirements.txt
python run.py
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Changelog

### Versão 2.0 (Atual)
- ✅ Tema laranja completo implementado
- ✅ Sistema de backup com Excel funcionando
- ✅ Interface moderna com Bootstrap 5
- ✅ Gráficos interativos com Chart.js
- ✅ Gestão completa de empenhos e contratos
- ✅ Sistema de autenticação robusto

### Versão 1.0
- ✅ Sistema básico de empenhos
- ✅ CRUD completo
- ✅ Relatórios básicos

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: [seu-email@domain.com]
- 🐛 Issues: [GitHub Issues](https://github.com/elneves81/gest-oempenhos/issues)
- 📚 Wiki: [GitHub Wiki](https://github.com/elneves81/gest-oempenhos/wiki)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Gestão de Empenhos e Contratos** - Sistema profissional para controle orçamentário e administrativo.
