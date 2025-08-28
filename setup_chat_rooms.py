#!/usr/bin/env python
"""
Script para criar as tabelas do sistema de chat com salas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models_chat_rooms import ChatRoom, ChatMember, ChatRoomMessage
from sqlalchemy import text

def create_chat_tables():
    """Cria as tabelas do sistema de chat"""
    with app.app_context():
        try:
            print("🔨 Criando tabelas do sistema de chat...")
            
            # Criar todas as tabelas
            db.create_all()
            
            # Verificar se as tabelas foram criadas
            conn = db.engine.connect()
            
            tables_to_check = ['chat_rooms', 'chat_members', 'chat_room_messages']
            for table_name in tables_to_check:
                result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
                if result.fetchone():
                    print(f"✅ Tabela {table_name} criada com sucesso!")
                else:
                    print(f"❌ Erro ao criar tabela {table_name}")
            
            # Criar índices únicos importantes
            try:
                # Índice único para dm_key (evitar DMs duplicadas)
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_chat_rooms_dm_key ON chat_rooms(dm_key)"))
                print("✅ Índice único dm_key criado!")
            except Exception as e:
                print(f"⚠️ Aviso ao criar índice dm_key: {e}")
            
            # Criar sala geral padrão se não existir
            geral_room = ChatRoom.query.filter_by(name='Chat Geral', kind='group').first()
            if not geral_room:
                # Buscar primeiro usuário admin para ser criador
                from models import User
                admin_user = User.query.filter_by(is_admin=True).first()
                if not admin_user:
                    # Se não tem admin, usar o primeiro usuário
                    admin_user = User.query.first()
                
                if admin_user:
                    geral_room = ChatRoom(
                        name='Chat Geral',
                        kind='group',
                        created_by=admin_user.id
                    )
                    db.session.add(geral_room)
                    db.session.commit()
                    print("✅ Sala 'Chat Geral' criada!")
                else:
                    print("⚠️ Nenhum usuário encontrado para criar sala geral")
            else:
                print("✅ Sala 'Chat Geral' já existe!")
            
            conn.close()
            print("🎉 Sistema de chat inicializado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_chat_tables()
