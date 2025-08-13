# Gestão de Empenhos e Contratos

Sistema web completo para gestão de empenhos e contratos públicos, desenvolvido em Python Flask com interface moderna e funcionalidades profissionais.

## 🚀 Características

- ✅ **Gestão Completa de Empenhos**: CRUD completo com validações
- ✅ **Controle de Contratos**: Gerenciamento de contratos e aditivos
- ✅ **Importação Inteligente**: Suporte a Excel/CSV com mapeamento automático
- ✅ **Exportação Profissional**: Relatórios em PDF e Excel
- ✅ **Dashboard Interativo**: Gráficos e estatísticas em tempo real
- ✅ **Sistema de Usuários**: Autenticação e controle de permissões
- ✅ **Cálculos Automáticos**: Valores líquidos, retenções e saldos
- ✅ **Interface Responsiva**: Design moderno com Bootstrap
- ✅ **Backup Automático**: Proteção dos dados

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

## 🔧 Instalação

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd empenhos
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o sistema
```bash
python run.py
```

### 4. Acesse o sistema
- URL: http://localhost:5000
- Login: `admin`
- Senha: `admin123`

## 📊 Funcionalidades Principais

### Dashboard
- Estatísticas gerais dos empenhos
- Gráficos interativos por status
- Empenhos recentes
- Ações rápidas

### Gestão de Empenhos
- **Criar**: Formulário completo com validações
- **Editar**: Atualização de dados existentes
- **Visualizar**: Detalhes completos do empenho
- **Excluir**: Remoção segura com confirmação
- **Filtrar**: Busca por múltiplos critérios
- **Paginar**: Navegação eficiente em grandes volumes

### Importação de Dados
- **Formatos Suportados**: Excel (.xlsx, .xls) e CSV
- **Mapeamento Automático**: Reconhece colunas automaticamente
- **Validação**: Verifica dados antes da importação
- **Relatório de Erros**: Detalha problemas encontrados
- **Template**: Modelo para facilitar importação

### Exportação e Relatórios
- **Excel**: Planilhas formatadas com resumos
- **PDF**: Relatórios profissionais
- **Filtros**: Exportação de dados específicos
- **Backup**: Cópia completa do sistema

### Sistema de Usuários
- **Autenticação**: Login seguro
- **Perfis**: Usuário comum e administrador
- **Gerenciamento**: Criação e controle de usuários
- **Auditoria**: Rastreamento de ações

## 📁 Estrutura do Projeto

```
empenhos/
├── app.py                 # Aplicação principal Flask
├── models.py              # Modelos do banco de dados
├── requirements.txt       # Dependências Python
├── run.py                 # Script de execução
├── setup.py              # Configuração inicial
├── routes/               # Rotas da aplicação
│   ├── auth.py           # Autenticação
│   ├── empenhos.py       # Gestão de empenhos
│   └── relatorios.py     # Relatórios e exportação
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── dashboard.html    # Dashboard principal
│   ├── auth/            # Templates de autenticação
│   ├── empenhos/        # Templates de empenhos
│   └── relatorios/      # Templates de relatórios
├── utils/               # Utilitários
│   ├── export.py        # Exportação de dados
│   └── import_data.py   # Importação de dados
├── uploads/             # Arquivos enviados
└── backups/             # Backups do sistema
```

## 🔄 Importação de Dados

### Preparando a Planilha

1. **Baixe o template** na página de importação
2. **Preencha os dados** seguindo o formato
3. **Campos obrigatórios**:
   - PREGAO
   - CTR (Contrato)
   - EMPENHO
   - VALOR_EMPENHADO
   - DATA_EMPENHO
   - OBJETO

### Colunas Reconhecidas

O sistema reconhece automaticamente estas colunas:

| Coluna na Planilha | Campo no Sistema |
|-------------------|------------------|
| PREGAO, PREGÃO | Número do Pregão |
| CTR, CONTRATO | Número do Contrato |
| EMPENHO | Número do Empenho |
| VALOR_EMPENHADO | Valor Empenhado |
| DATA_EMPENHO | Data do Empenho |
| OBJETO | Objeto do Contrato |
| QTD, QUANTIDADE | Quantidade |
| RETENCAO | Percentual de Retenção |
| STATUS, SITUACAO | Status |

### Formatos de Data
- DD/MM/AAAA (01/12/2024)
- DD-MM-AAAA (01-12-2024)
- AAAA-MM-DD (2024-12-01)

### Formatos de Valor
- 1000.50
- 1.000,50
- R$ 1.000,50

## 📈 Relatórios

### Dashboard de Relatórios
- Estatísticas consolidadas
- Gráficos por status e período
- Top contratos por valor

### Relatórios Filtrados
- Filtro por período
- Filtro por status
- Filtro por contrato/pregão
- Exportação dos resultados

### Exportação
- **Excel**: Dados completos + resumo
- **PDF**: Relatório formatado
- **Backup**: Cópia completa do sistema

## 👥 Gerenciamento de Usuários

### Tipos de Usuário
- **Administrador**: Acesso completo
- **Usuário**: Acesso limitado

### Funcionalidades Admin
- Criar novos usuários
- Ativar/desativar usuários
- Fazer backup do sistema
- Visualizar todos os dados

## 🔒 Segurança

- Senhas criptografadas
- Sessões seguras
- Validação de dados
- Controle de acesso
- Auditoria de ações

## 🛠️ Personalização

### Modificar Interface
Edite os arquivos em `templates/` para personalizar a aparência.

### Adicionar Campos
1. Modifique `models.py`
2. Atualize os templates
3. Ajuste as rotas conforme necessário

### Configurar Email (Opcional)
Edite as configurações no `app.py` para notificações por email.

## 🐛 Solução de Problemas

### Erro de Importação
- Verifique se todas as dependências estão instaladas
- Execute: `pip install -r requirements.txt`

### Erro de Banco de Dados
- Delete o arquivo `empenhos.db`
- Execute novamente: `python run.py`

### Erro de Permissão
- Verifique se tem permissão de escrita na pasta
- Execute como administrador se necessário

### Problemas de Importação
- Use o template fornecido
- Verifique o formato das datas
- Certifique-se que campos obrigatórios estão preenchidos

## 📞 Suporte

Para dúvidas ou problemas:

1. Verifique os logs em `logs/`
2. Consulte este README
3. Verifique se seguiu todos os passos de instalação

## 🔄 Atualizações

Para atualizar o sistema:

1. Faça backup dos dados
2. Substitua os arquivos
3. Execute: `pip install -r requirements.txt`
4. Reinicie o sistema

## 📝 Licença

Este sistema foi desenvolvido para uso interno e gerenciamento de empenhos públicos.

---

**Desenvolvido com ❤️ para facilitar a gestão de empenhos públicos**
