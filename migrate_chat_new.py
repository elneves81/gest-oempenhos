#!/usr/bin/env python3
"""
Script para migrar/criar as novas tabelas de chat
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db
from models_chat import ChatRoom, ChatMember, ChatMessage, ChatAttachment

def migrate_chat_tables():
    """Cria as novas tabelas de chat"""
    
    with app.app_context():
        print("🔄 Iniciando migração das tabelas de chat...")
        
        try:
            # Verificar se as tabelas já existem
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📋 Tabelas existentes: {existing_tables}")
            
            # Criar as novas tabelas
            print("🆕 Criando novas tabelas de chat...")
            
            # Criar todas as tabelas definidas nos modelos
            db.create_all()
            
            # Verificar se foram criadas
            inspector = db.inspect(db.engine)
            new_tables = inspector.get_table_names()
            
            print(f"✅ Tabelas após migração: {new_tables}")
            
            # Verificar especificamente as tabelas de chat
            chat_tables = ['chat_rooms', 'chat_members', 'chat_messages', 'chat_attachments']
            
            for table in chat_tables:
                if table in new_tables:
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    print(f"✅ {table}: {columns}")
                else:
                    print(f"❌ {table}: NÃO CRIADA")
            
            print("🎉 Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            return False
            
    return True

if __name__ == "__main__":
    migrate_chat_tables()
