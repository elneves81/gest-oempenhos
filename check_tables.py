import sqlite3
import os

# Caminho para o banco de dados
db_path = "empenhos.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tabelas existentes no banco:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Verificar se as tabelas de chat existem
    chat_tables = ['chat_rooms', 'chat_members', 'chat_messages', 'chat_attachments']
    existing_chat_tables = [table[0] for table in tables]
    
    print("\nStatus das tabelas de chat:")
    for chat_table in chat_tables:
        if chat_table in existing_chat_tables:
            print(f"✅ {chat_table} - EXISTS")
            # Mostrar estrutura da tabela
            cursor.execute(f"PRAGMA table_info({chat_table});")
            columns = cursor.fetchall()
            print(f"   Colunas: {[col[1] for col in columns]}")
        else:
            print(f"❌ {chat_table} - NOT EXISTS")
    
    conn.close()
else:
    print("Banco de dados não encontrado!")
