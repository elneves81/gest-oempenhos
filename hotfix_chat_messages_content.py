#!/usr/bin/env python3
"""
🔧 HOTFIX: Adicionar coluna 'content' na tabela chat_room_messages
Resolve erro: sqlalchemy.exc.OperationalError: no such column: chat_room_messages.content
"""

import sqlite3
import os
from sqlalchemy import create_engine, text

def col_exists(conn, table_name, column_name):
    """Verifica se a coluna existe na tabela"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def main():
    db_path = 'empenhos.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados {db_path} não encontrado!")
        return
    
    # Conectar usando SQLite direto
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Verificando estrutura da tabela chat_room_messages...")
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_room_messages'")
        if not cursor.fetchone():
            print("⚠️ Tabela chat_room_messages não encontrada! Criando...")
            # Criar a tabela completa se não existir
            cursor.execute("""
                CREATE TABLE chat_room_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (room_id) REFERENCES chat_rooms(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("✅ Tabela chat_room_messages criada com sucesso!")
        else:
            print("✅ Tabela chat_room_messages encontrada")
            
            # Verificar e adicionar coluna 'content' se não existir
            if not col_exists(conn, 'chat_room_messages', 'content'):
                print("🔧 Adicionando coluna 'content'...")
                cursor.execute("ALTER TABLE chat_room_messages ADD COLUMN content TEXT")
                print("✅ Coluna 'content' adicionada!")
                
                # Migrar dados de 'text' para 'content' se 'text' existe e tem dados
                if col_exists(conn, 'chat_room_messages', 'text'):
                    print("🔄 Migrando dados de 'text' para 'content'...")
                    cursor.execute("UPDATE chat_room_messages SET content = text WHERE content IS NULL AND text IS NOT NULL")
                    migrated = cursor.rowcount
                    print(f"✅ {migrated} mensagens migradas de 'text' para 'content'")
            else:
                print("✅ Coluna 'content' já existe!")
                
            # Verificar outras colunas necessárias
            if not col_exists(conn, 'chat_room_messages', 'deleted'):
                print("🔧 Adicionando coluna 'deleted'...")
                cursor.execute("ALTER TABLE chat_room_messages ADD COLUMN deleted INTEGER DEFAULT 0")
                print("✅ Coluna 'deleted' adicionada!")
                
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(chat_room_messages)")
        columns = cursor.fetchall()
        print("\n📋 Estrutura final da tabela chat_room_messages:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        # Commit das mudanças
        conn.commit()
        print("\n🎉 Hotfix aplicado com sucesso!")
        print("🔄 Reinicie o servidor para aplicar as mudanças")
        
    except Exception as e:
        print(f"❌ Erro ao aplicar hotfix: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
