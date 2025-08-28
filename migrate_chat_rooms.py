#!/usr/bin/env python
"""
Script para migrar/atualizar as tabelas do sistema de chat
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

def migrate_chat_tables():
    """Migra/atualiza as tabelas do sistema de chat"""
    with app.app_context():
        try:
            print("🔄 Verificando e atualizando tabelas do sistema de chat...")
            
            conn = db.engine.connect()
            
            # Verificar e adicionar colunas que faltam na chat_rooms
            try:
                # Verificar se updated_at existe
                result = conn.execute(text("PRAGMA table_info(chat_rooms)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE chat_rooms ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP"))
                    print("✅ Coluna updated_at adicionada à chat_rooms")
                
                # Verificar se dm_key tem índice único
                try:
                    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_chat_rooms_dm_key ON chat_rooms(dm_key)"))
                    print("✅ Índice único dm_key criado/verificado")
                except Exception as e:
                    print(f"⚠️ Aviso ao criar índice dm_key: {e}")
            
            except Exception as e:
                print(f"⚠️ Erro ao atualizar chat_rooms: {e}")
            
            # Verificar se tabela chat_members existe
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_members'"))
            if not result.fetchone():
                print("🔨 Criando tabela chat_members...")
                conn.execute(text("""
                    CREATE TABLE chat_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'member',
                        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(room_id, user_id)
                    )
                """))
                print("✅ Tabela chat_members criada!")
            else:
                print("✅ Tabela chat_members já existe")
            
            # Verificar se tabela chat_room_messages existe
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_room_messages'"))
            if not result.fetchone():
                print("🔨 Criando tabela chat_room_messages...")
                conn.execute(text("""
                    CREATE TABLE chat_room_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        text TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        deleted BOOLEAN DEFAULT 0,
                        FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """))
                print("✅ Tabela chat_room_messages criada!")
            else:
                print("✅ Tabela chat_room_messages já existe")
            
            # Criar índices para performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_chat_members_room_id ON chat_members(room_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_members_user_id ON chat_members(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_room_messages_room_id ON chat_room_messages(room_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_room_messages_user_id ON chat_room_messages(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_room_messages_created_at ON chat_room_messages(created_at)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    print(f"⚠️ Aviso ao criar índice: {e}")
            
            print("✅ Índices de performance criados!")
            
            # Verificar se sala geral existe
            result = conn.execute(text("SELECT * FROM chat_rooms WHERE name = 'Chat Geral' LIMIT 1"))
            if not result.fetchone():
                # Buscar primeiro usuário para ser criador
                result = conn.execute(text("SELECT id FROM users WHERE is_admin = 1 LIMIT 1"))
                admin_user = result.fetchone()
                if not admin_user:
                    result = conn.execute(text("SELECT id FROM users LIMIT 1"))
                    admin_user = result.fetchone()
                
                if admin_user:
                    user_id = admin_user[0]
                    conn.execute(text("""
                        INSERT INTO chat_rooms (name, kind, created_by, created_at)
                        VALUES (:name, :kind, :user_id, CURRENT_TIMESTAMP)
                    """), {"name": "Chat Geral", "kind": "group", "user_id": user_id})
                    print("✅ Sala 'Chat Geral' criada!")
                else:
                    print("⚠️ Nenhum usuário encontrado para criar sala geral")
            else:
                print("✅ Sala 'Chat Geral' já existe!")
            
            # Commit das mudanças
            conn.commit()
            conn.close()
            
            print("🎉 Sistema de chat migrado/atualizado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    migrate_chat_tables()
