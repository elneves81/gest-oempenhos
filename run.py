#!/usr/bin/env python3
"""
Script simples para executar o Sistema de Empenhos
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Cria diretórios necessários"""
    directories = ["uploads", "backups", "logs", "instance"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def main():
    """Função principal"""
    print("🚀 Iniciando Gestão de Empenhos e Contratos...")
    
    # Criar diretórios necessários
    create_directories()
    
    # Importar e executar a aplicação
    try:
        from app import app, create_tables
        
        # Criar tabelas se necessário
        create_tables()
        
        print("✅ Sistema inicializado com sucesso!")
        print("📍 Acesse: http://localhost:5000")
        print("🔑 Login padrão: admin / admin123")
        print("⏹️  Pressione Ctrl+C para parar")
        print("-" * 50)
        
        # Executar aplicação
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
