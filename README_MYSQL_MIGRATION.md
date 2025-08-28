# 🚀 MIGRAÇÃO PARA XAMPP + MYSQL

Sistema completo migrado do SQLite para MySQL (XAMPP) com dois aplicativos separados que se comunicam através do mesmo banco de dados.

## 📋 PRÉ-REQUISITOS

1. **XAMPP instalado** - https://www.apachefriends.org/
2. **Dependências Python instaladas** ✅ (já feito)
3. **MySQL rodando no XAMPP**

## 🔧 PASSOS DA MIGRAÇÃO

### 1. Configurar XAMPP
```bash
# 1. Abrir painel do XAMPP
# 2. Iniciar Apache e MySQL
# 3. Verificar se está rodando: http://localhost/phpmyadmin
```

### 2. Criar Banco de Dados
```sql
-- Opção A: Via phpMyAdmin
-- Acesse: http://localhost/phpmyadmin
-- Execute o arquivo: setup_mysql_database.sql

-- Opção B: Comando direto
CREATE DATABASE IF NOT EXISTS chat_empenhos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 3. Migrar Dados (Opcional)
```bash
# Se você tem dados no SQLite para migrar:
python migrate_to_mysql.py
```

### 4. Iniciar Aplicações

#### Sistema Principal (Dashboard + Empenhos)
```bash
python app_mysql_principal.py
# Acesso: http://localhost:5001
# Login: admin / admin123
```

#### Chat MSN Style
```bash
python app_mysql_chat.py  
# Acesso: http://localhost:5002
# Login: mesmo usuário do sistema principal
```

## 🎯 FUNCIONALIDADES

### Sistema Principal (Porta 5001)
- ✅ Dashboard com widgets drag-and-drop
- ✅ Busca avançada (Empenhos, Contratos, Notas Fiscais)
- ✅ KPIs em tempo real
- ✅ Autenticação integrada
- ✅ MySQL como banco principal

### Chat MSN Style (Porta 5002)
- ✅ Interface nostálgica do MSN Messenger
- ✅ Salas de chat múltiplas
- ✅ Anexo de arquivos (PDF, DOC, IMG)
- ✅ Usuários compartilhados com sistema principal
- ✅ Banco MySQL integrado

## 🔗 COMUNICAÇÃO ENTRE SISTEMAS

Os dois sistemas se comunicam através do **mesmo banco MySQL**:

```
┌─────────────────────┐    ┌─────────────────────┐
│   Sistema Principal │    │    Chat MSN Style   │
│   (porta 5001)      │    │    (porta 5002)     │
└──────────┬──────────┘    └──────────┬──────────┘
           │                          │
           └──────────┬─────────────────┘
                      │
           ┌──────────▼──────────┐
           │    MySQL Database   │
           │   (chat_empenhos)   │
           └─────────────────────┘
```

### Tabelas Compartilhadas:
- `users` - Usuários do sistema
- `empenho` - Dados de empenhos  
- `contrato` - Dados de contratos
- `nota_fiscal` - Notas fiscais

### Tabelas Específicas do Chat:
- `chat_msn_room` - Salas de chat
- `chat_msn_message` - Mensagens
- `chat_msn_attachment` - Anexos

## 🚀 COMANDOS RÁPIDOS

```bash
# Instalar dependências (já feito)
python install_mysql_deps.py

# Migrar dados do SQLite (se necessário)
python migrate_to_mysql.py

# Iniciar sistema principal
python app_mysql_principal.py

# Iniciar chat (em outro terminal)
python app_mysql_chat.py
```

## 📊 ENDEREÇOS

| Sistema | URL | Porta | Função |
|---------|-----|-------|--------|
| Dashboard | http://localhost:5001/dashboard | 5001 | Widgets e KPIs |
| Login Principal | http://localhost:5001/login | 5001 | Autenticação |
| Chat MSN | http://localhost:5002/chat | 5002 | Chat nostálgico |
| Login Chat | http://localhost:5002/login | 5002 | Acesso ao chat |
| phpMyAdmin | http://localhost/phpmyadmin | 80 | Gerenciar MySQL |

## ⚡ RECURSOS AVANÇADOS

### Dashboard Widgets
- Drag & Drop com GridStack
- Busca individual por entidade
- KPIs automáticos
- Responsive design

### Chat MSN Features  
- Interface retrô do MSN
- Upload de arquivos
- Salas múltiplas
- Mensagens em tempo real
- Integração com usuários

### Banco MySQL
- UTF-8 completo (utf8mb4)
- Conexão persistente
- Auto-reconnect
- Backup automático

## 🔧 TROUBLESHOOTING

### MySQL não conecta?
```bash
# Verificar se XAMPP está rodando
# Painel XAMPP > MySQL > Start

# Testar conexão
mysql -u root -p
```

### Erro nas dependências?
```bash
pip install mysql-connector-python PyMySQL
```

### Dados não aparecem?
```bash
# Executar migração
python migrate_to_mysql.py

# Ou criar dados de teste manualmente
```

## ✅ STATUS

- [x] Dependências MySQL instaladas
- [x] Scripts de migração criados  
- [x] Sistema principal adaptado para MySQL
- [x] Chat MSN adaptado para MySQL
- [x] Comunicação entre sistemas via banco
- [x] Templates e autenticação
- [x] Documentação completa

## 🎉 PRÓXIMOS PASSOS

1. **Iniciar XAMPP e MySQL**
2. **Criar banco de dados**
3. **Executar os dois sistemas**
4. **Testar integração**

Os sistemas agora estão **separados mas comunicando** através do MySQL! 🚀
