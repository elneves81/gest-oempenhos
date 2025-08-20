#!/usr/bin/env python3
"""
Script simples para criar tabelas do chat
"""

import sys
import os

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa os modelos do chat
from models_chat import db, ChatSession, ChatMessage

# Configuração de banco direto
import sqlite3

def create_chat_tables():
    """Cria as tabelas do chat diretamente no SQLite"""
    
    db_path = os.path.join('instance', 'empenhos.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Cria tabela chat_sessions se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) DEFAULT 'Nova Conversa',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Cria tabela chat_messages se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                is_from_user BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Tabelas do chat criadas com sucesso!")
        
        # Verifica se as tabelas foram criadas
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chat_%'")
        tables = cursor.fetchall()
        
        print(f"📋 Tabelas encontradas: {[table[0] for table in tables]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == '__main__':
    create_chat_tables()
