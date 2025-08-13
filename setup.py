#!/usr/bin/env python3
"""
Script de configuração inicial do Sistema de Empenhos
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Imprime cabeçalho do setup"""
    print("=" * 60)
    print("    SISTEMA DE EMPENHOS - CONFIGURAÇÃO INICIAL")
    print("=" * 60)
    print()

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    print("🔍 Verificando versão do Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário!")
        print(f"   Versão atual: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def install_dependencies():
    """Instala as dependências do projeto"""
    print("\n📦 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def create_directories():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    directories = [
        "uploads",
        "backups",
        "logs",
        "instance"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Diretório '{directory}' criado/verificado")

def create_env_file():
    """Cria arquivo de configuração .env"""
    print("\n⚙️  Criando arquivo de configuração...")
    
    env_content = """# Configurações do Sistema de Empenhos
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-muito-segura-aqui-mude-em-producao
DATABASE_URL=sqlite:///empenhos.db

# Configurações de Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads

# Configurações de Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app

# Configurações de Backup
BACKUP_FOLDER=backups
AUTO_BACKUP=True
BACKUP_RETENTION_DAYS=30
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Arquivo .env criado")
    else:
        print("ℹ️  Arquivo .env já existe")

def initialize_database():
    """Inicializa o banco de dados"""
    print("\n🗄️  Inicializando banco de dados...")
    try:
        # Importar e executar a função de criação de tabelas
        from app import create_tables
        create_tables()
        print("✅ Banco de dados inicializado com sucesso!")
        print("   Usuário admin criado: admin / admin123")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

def create_startup_scripts():
    """Cria scripts de inicialização"""
    print("\n📜 Criando scripts de inicialização...")
    
    # Script para Windows
    windows_script = """@echo off
echo Iniciando Sistema de Empenhos...
python app.py
pause
"""
    
    with open('start_windows.bat', 'w', encoding='utf-8') as f:
        f.write(windows_script)
    
    # Script para Linux/Mac
    unix_script = """#!/bin/bash
echo "Iniciando Sistema de Empenhos..."
python3 app.py
"""
    
    with open('start_unix.sh', 'w', encoding='utf-8') as f:
        f.write(unix_script)
    
    # Tornar executável no Unix
    try:
        os.chmod('start_unix.sh', 0o755)
    except:
        pass
    
    print("✅ Scripts de inicialização criados")

def create_readme():
    """Cria arquivo README com instruções"""
    print("\n📖 Criando documentação...")
    
    readme_content = """# Sistema de Empenhos

Sistema web completo para gestão de empenhos e contratos.

## 🚀 Como Usar

### Primeira Execução
1. Execute o setup: `python setup.py`
2. Inicie o sistema: `python app.py`
3. Acesse: http://localhost:5000
4. Login: admin / admin123

### Funcionalidades
- ✅ Gestão completa de empenhos
- ✅ Controle de contratos
- ✅ Importação de planilhas Excel/CSV
- ✅ Exportação para PDF/Excel
- ✅ Relatórios e dashboards
- ✅ Sistema de usuários
- ✅ Cálculos automáticos
- ✅ Backup automático

### Estrutura do Projeto
```
empenhos/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
├── models/            # Modelos do banco
├── routes/            # Rotas da aplicação
├── templates/         # Templates HTML
├── utils/             # Utilitários
├── uploads/           # Arquivos enviados
└── backups/           # Backups do sistema
```

### Importação de Dados
1. Baixe o template na página de importação
2. Preencha os dados seguindo o formato
3. Faça upload do arquivo
4. Verifique os resultados

### Backup e Restauração
- Backups automáticos são criados diariamente
- Use a função "Backup do Sistema" no menu admin
- Arquivos ficam na pasta `backups/`

### Suporte
Para dúvidas ou problemas, consulte os logs em `logs/` ou contate o administrador.

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)
- `SECRET_KEY`: Chave secreta da aplicação
- `DATABASE_URL`: URL do banco de dados
- `UPLOAD_FOLDER`: Pasta para uploads
- `BACKUP_FOLDER`: Pasta para backups

### Personalização
- Modifique `templates/` para alterar a interface
- Ajuste `models/` para novos campos
- Configure `utils/` para novas funcionalidades

## 📊 Relatórios Disponíveis
- Dashboard com estatísticas
- Relatórios filtrados por período/status
- Exportação em Excel e PDF
- Gráficos interativos

## 🔐 Segurança
- Autenticação de usuários
- Controle de permissões
- Validação de dados
- Backup automático
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README.md criado")

def print_success():
    """Imprime mensagem de sucesso"""
    print("\n" + "=" * 60)
    print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("📋 Próximos passos:")
    print("   1. Execute: python app.py")
    print("   2. Acesse: http://localhost:5000")
    print("   3. Login: admin / admin123")
    print()
    print("📁 Arquivos criados:")
    print("   • .env (configurações)")
    print("   • README.md (documentação)")
    print("   • start_windows.bat (Windows)")
    print("   • start_unix.sh (Linux/Mac)")
    print()
    print("🔧 Para personalizar, edite o arquivo .env")
    print("📖 Consulte o README.md para mais informações")
    print()

def main():
    """Função principal do setup"""
    print_header()
    
    # Verificações e instalações
    if not check_python_version():
        return False
    
    if not install_dependencies():
        return False
    
    create_directories()
    create_env_file()
    
    if not initialize_database():
        return False
    
    create_startup_scripts()
    create_readme()
    
    print_success()
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Setup falhou. Verifique os erros acima.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
