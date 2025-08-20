#!/usr/bin/env python3
"""
Inicializa o banco de dados com todas as tabelas necessárias
"""

import os
import sys
from app import app
from models import db

def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    
    print("🚀 INICIALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Verificar se o diretório instance existe
            instance_dir = os.path.join(os.getcwd(), 'instance')
            if not os.path.exists(instance_dir):
                os.makedirs(instance_dir)
                print(f"✅ Diretório criado: {instance_dir}")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Todas as tabelas criadas com sucesso!")
            
            # Verificar se o banco foi criado
            db_path = os.path.join(instance_dir, 'empenhos.db')
            if os.path.exists(db_path):
                print(f"✅ Banco de dados criado: {db_path}")
                print(f"📊 Tamanho: {os.path.getsize(db_path)} bytes")
                
                # Listar tabelas criadas
                with db.engine.connect() as conn:
                    result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = [row[0] for row in result]
                print(f"📋 Tabelas criadas: {', '.join(tables)}")
                
                return True
            else:
                print("❌ Banco de dados não foi criado!")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao criar banco: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_database()
    if not success:
        sys.exit(1)
    print("\n✅ Inicialização concluída com sucesso!")
