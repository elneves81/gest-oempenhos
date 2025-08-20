#!/usr/bin/env python3
"""
Script para corrigir a estrutura das tabelas do chat
"""

import sqlite3
import os

def fix_chat_database():
    db_path = 'instance/empenhos.db'
    
    if not os.path.exists(db_path):
        print("❌ Database não encontrado:", db_path)
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Recriando tabelas do chat com estrutura correta...")
        
        # Remover tabelas antigas
        cursor.execute("DROP TABLE IF EXISTS chat_messages")
        cursor.execute("DROP TABLE IF EXISTS chat_sessions")
        print("🗑️ Tabelas antigas removidas")
        
        # Criar chat_sessions
        cursor.execute('''
            CREATE TABLE chat_sessions (
                id VARCHAR(100) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) DEFAULT 'Nova Conversa',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Tabela chat_sessions criada")
        
        # Criar chat_messages
        cursor.execute('''
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(100),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
            )
        ''')
        print("✅ Tabela chat_messages criada")
        
        conn.commit()
        print("\n🎉 Tabelas do chat recriadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao corrigir database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_chat_database()
