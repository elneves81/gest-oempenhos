#!/usr/bin/env python3
"""
Script para instalar dependências MySQL e configurar XAMPP
"""

import subprocess
import sys
import os

def install_mysql_dependencies():
    """Instala as dependências necessárias para MySQL"""
    print("🔧 Instalando dependências MySQL...")
    
    packages = [
        'mysql-connector-python',
        'PyMySQL',
        'cryptography'  # Necessário para PyMySQL
    ]
    
    for package in packages:
        try:
            print(f"📦 Instalando {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} instalado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            return False
    
    return True

def create_mysql_database_script():
    """Cria script SQL para criar o banco de dados"""
    sql_script = """
-- Script para criar banco de dados no XAMPP/MySQL
-- Execute este script no phpMyAdmin ou MySQL Workbench

-- 1. Criar banco de dados
CREATE DATABASE IF NOT EXISTS chat_empenhos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. Usar o banco
USE chat_empenhos;

-- 3. Criar usuário específico (opcional)
-- CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'chat_password';
-- GRANT ALL PRIVILEGES ON chat_empenhos.* TO 'chat_user'@'localhost';
-- FLUSH PRIVILEGES;

-- 4. Tabelas serão criadas automaticamente pelo SQLAlchemy

-- Verificar se foi criado
SHOW DATABASES LIKE 'chat_empenhos';
"""
    
    with open('setup_mysql_database.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("✅ Script SQL criado: setup_mysql_database.sql")

def main():
    print("🚀 CONFIGURAÇÃO XAMPP + MYSQL")
    print("=" * 50)
    
    print("\n📋 Passo 1: Verificar XAMPP")
    print("- Certifique-se que o XAMPP está instalado")
    print("- Inicie o Apache e MySQL no painel do XAMPP")
    print("- Acesse: http://localhost/phpmyadmin")
    
    print("\n📋 Passo 2: Instalar dependências Python")
    if install_mysql_dependencies():
        print("✅ Dependências instaladas com sucesso!")
    else:
        print("❌ Erro ao instalar dependências")
        return
    
    print("\n📋 Passo 3: Criar script de banco")
    create_mysql_database_script()
    
    print("\n📋 Passo 4: Instruções finais")
    print("1. Abra phpMyAdmin: http://localhost/phpmyadmin")
    print("2. Execute o script: setup_mysql_database.sql")
    print("3. Ou crie manualmente o banco 'chat_empenhos'")
    print("4. Configure a senha do MySQL se necessário")
    
    print("\n🎯 Próximos passos:")
    print("- python app_mysql_principal.py (porta 5001)")
    print("- python app_mysql_chat.py (porta 5002)")
    print("- Os dois sistemas vão usar o mesmo banco MySQL!")
    
    print("\n✅ Configuração concluída!")

if __name__ == "__main__":
    main()
