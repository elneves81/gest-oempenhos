#!/usr/bin/env python
"""
Script para verificar e migrar a estrutura da tabela chat_rooms
"""

import sqlite3
import sys
import os

def check_and_migrate_chat_rooms():
    """Verifica e migra a tabela chat_rooms"""
    try:
        conn = sqlite3.connect('empenhos.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_rooms'")
        if not cursor.fetchone():
            print("❌ Tabela chat_rooms não existe")
            return
        
        # Verificar colunas atuais
        cursor.execute('PRAGMA table_info(chat_rooms)')
        cols = cursor.fetchall()
        current_columns = [row[1] for row in cols]
        
        print("📋 Colunas atuais da tabela chat_rooms:")
        for row in cols:
            print(f"  {row[1]} {row[2]} {'NOT NULL' if row[3] else ''} {'PRIMARY KEY' if row[5] else ''}")
        
        # Colunas necessárias
        required_columns = {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'VARCHAR(200) NOT NULL',
            'kind': 'VARCHAR(10) NOT NULL DEFAULT "group"',
            'dm_key': 'VARCHAR(50) UNIQUE',
            'created_by': 'INTEGER NOT NULL',
            'created_at': 'DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        }
        
        # Verificar quais colunas estão faltando
        missing_columns = []
        for col_name, col_def in required_columns.items():
            if col_name not in current_columns:
                missing_columns.append((col_name, col_def))
        
        if missing_columns:
            print(f"\n🔧 Adicionando {len(missing_columns)} colunas faltantes:")
            for col_name, col_def in missing_columns:
                try:
                    # Para SQLite, precisamos usar ALTER TABLE ADD COLUMN
                    if col_name == 'kind':
                        cursor.execute(f'ALTER TABLE chat_rooms ADD COLUMN {col_name} VARCHAR(10) NOT NULL DEFAULT "group"')
                    elif col_name == 'dm_key':
                        cursor.execute(f'ALTER TABLE chat_rooms ADD COLUMN {col_name} VARCHAR(50)')
                    elif col_name == 'updated_at':
                        cursor.execute(f'ALTER TABLE chat_rooms ADD COLUMN {col_name} DATETIME DEFAULT CURRENT_TIMESTAMP')
                    else:
                        # Para outras colunas, usar a definição completa
                        cursor.execute(f'ALTER TABLE chat_rooms ADD COLUMN {col_name} {col_def.split(" ", 1)[1] if " " in col_def else col_def}')
                    
                    print(f"  ✅ Coluna {col_name} adicionada")
                except Exception as e:
                    print(f"  ❌ Erro ao adicionar coluna {col_name}: {e}")
        else:
            print("\n✅ Todas as colunas necessárias já existem!")
        
        # Verificar se precisamos criar outras tabelas
        tables_to_create = ['chat_members', 'chat_room_messages']
        for table_name in tables_to_create:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"\n🔨 Criando tabela {table_name}...")
                if table_name == 'chat_members':
                    cursor.execute("""
                        CREATE TABLE chat_members (
                            id INTEGER PRIMARY KEY,
                            room_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            role VARCHAR(20) NOT NULL DEFAULT 'member',
                            joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                            UNIQUE(room_id, user_id)
                        )
                    """)
                elif table_name == 'chat_room_messages':
                    cursor.execute("""
                        CREATE TABLE chat_room_messages (
                            id INTEGER PRIMARY KEY,
                            room_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            text TEXT,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            deleted BOOLEAN NOT NULL DEFAULT 0,
                            FOREIGN KEY (room_id) REFERENCES chat_rooms (id) ON DELETE CASCADE,
                            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                        )
                    """)
                print(f"  ✅ Tabela {table_name} criada!")
            else:
                print(f"  ✅ Tabela {table_name} já existe!")
        
        # Criar índices importantes
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_chat_rooms_dm_key ON chat_rooms(dm_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_members_room_id ON chat_members(room_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_members_user_id ON chat_members(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_room_messages_room_id ON chat_room_messages(room_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_room_messages_user_id ON chat_room_messages(user_id)")
            print("✅ Índices criados!")
        except Exception as e:
            print(f"⚠️ Aviso ao criar índices: {e}")
        
        conn.commit()
        conn.close()
        print("\n🎉 Migração da estrutura de chat concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_migrate_chat_rooms()
