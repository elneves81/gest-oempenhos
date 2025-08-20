#!/usr/bin/env python3
"""
Script para migrar o banco de dados adicionando os novos campos do contrato
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

def create_app():
    """Criar aplicação Flask para migração"""
    app = Flask(__name__)
    
    # Configurações essenciais
    app.config['SECRET_KEY'] = 'dev-key-for-migration'
    
    # Usar caminho absoluto para o banco
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'empenhos.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def migrate_database():
    """Aplica as migrações necessárias no banco de dados"""
    
    app = create_app()
    db = SQLAlchemy(app)
    
    with app.app_context():
        try:
            # Verificar se as colunas já existem
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('contratos')]
            
            # Lista de novos campos para adicionar
            new_fields = [
                ('data_pregao', 'DATE'),
                ('data_contrato', 'DATE'), 
                ('data_processo', 'DATE'),
                ('digito_verificador', 'VARCHAR(10)'),
                ('tipo_contratacao', 'VARCHAR(50)')
            ]
            
            print("🔄 Iniciando migração do banco de dados...")
            
            # Adicionar campos que não existem
            changes_made = False
            for field_name, field_type in new_fields:
                if field_name not in columns:
                    print(f"➕ Adicionando campo: {field_name}")
                    db.session.execute(text(f'ALTER TABLE contratos ADD COLUMN {field_name} {field_type}'))
                    changes_made = True
                else:
                    print(f"✅ Campo já existe: {field_name}")
            
            if changes_made:
                # Commit das alterações
                db.session.commit()
                print("✅ Migração concluída com sucesso!")
            else:
                print("ℹ️  Nenhuma alteração necessária - todos os campos já existem")
            
            # Verificar a estrutura final
            print("\n📋 Campos relacionados aos novos recursos:")
            inspector = db.inspect(db.engine)  # Refresh do inspector
            final_columns = [column['name'] for column in inspector.get_columns('contratos')]
            for field_name, _ in new_fields:
                status = "✅" if field_name in final_columns else "❌"
                print(f"   {status} {field_name}")
                
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 Script de Migração do Banco de Dados")
    print("=" * 50)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migração executada com sucesso!")
        print("💡 Você pode agora usar os novos campos nos contratos:")
        print("   • Data do Pregão")
        print("   • Data do Contrato") 
        print("   • Data do Processo")
        print("   • Dígito Verificador")
        print("   • Tipo de Contratação")
    else:
        print("\n💥 Falha na migração!")
        print("🔧 Verifique os logs de erro acima.")
        sys.exit(1)
