#!/usr/bin/env python3
"""
Script para corrigir definitivamente as tabelas de chat no banco correto
"""

import sqlite3
import uuid
import os
from datetime import datetime

def fix_instance_chat_tables():
    banco = 'instance/empenhos.db'
    
    if not os.path.exists(banco):
        print(f"❌ Banco {banco} não existe!")
        return False
    
    conn = sqlite3.connect(banco)
    cursor = conn.cursor()
    
    try:
        print(f"🔧 Corrigindo tabelas de chat em {banco}...")
        
        # Verificar estrutura atual
        cursor.execute("PRAGMA table_info(chat_sessions)")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"📋 Colunas atuais em chat_sessions: {cols}")
        
        # Adicionar session_id se não existir
        if 'session_id' not in cols:
            print("🔨 Adicionando coluna session_id...")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN session_id VARCHAR(100)")
            conn.commit()
            print("✅ Coluna session_id adicionada!")
        else:
            print("ℹ️ Coluna session_id já existe")
        
        # Popular session_id para registros sem valor
        cursor.execute("SELECT id, session_id FROM chat_sessions WHERE session_id IS NULL OR session_id = ''")
        sessions_sem_id = cursor.fetchall()
        
        if sessions_sem_id:
            print(f"🔄 Populando session_id para {len(sessions_sem_id)} sessão(ões)...")
            for session_id, _ in sessions_sem_id:
                new_session_id = str(uuid.uuid4())
                cursor.execute("UPDATE chat_sessions SET session_id = ? WHERE id = ?", (new_session_id, session_id))
            conn.commit()
            print("✅ session_id populado!")
        else:
            print("ℹ️ Todas as sessões já têm session_id")
        
        # Verificar se última coluna é last_message_at ou updated_at
        if 'last_message_at' not in cols and 'updated_at' in cols:
            print("🔄 Renomeando updated_at para last_message_at...")
            # SQLite não suporta RENAME COLUMN facilmente, vamos criar nova tabela
            cursor.execute("""
                CREATE TABLE chat_sessions_new (
                    id INTEGER PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(200) DEFAULT 'Nova Conversa',
                    created_at DATETIME,
                    last_message_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Copiar dados
            cursor.execute("""
                INSERT INTO chat_sessions_new (id, session_id, user_id, title, created_at, last_message_at)
                SELECT id, session_id, user_id, title, created_at, updated_at FROM chat_sessions
            """)
            
            # Substituir tabela
            cursor.execute("DROP TABLE chat_sessions")
            cursor.execute("ALTER TABLE chat_sessions_new RENAME TO chat_sessions")
            conn.commit()
            print("✅ Coluna renomeada para last_message_at!")
        
        # Criar índices
        print("📊 Criando índices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)",
            "CREATE INDEX IF NOT EXISTS ix_chat_sessions_session_id ON chat_sessions (session_id)", 
            "CREATE INDEX IF NOT EXISTS ix_chat_sessions_last_message_at ON chat_sessions (last_message_at)",
            "CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages (session_id)",
            "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id ON chat_messages (user_id)"
        ]
        
        for idx in indices:
            cursor.execute(idx)
        conn.commit()
        print("✅ Índices criados!")
        
        # Verificar estrutura final
        print("\n📋 Estrutura final das tabelas:")
        cursor.execute("PRAGMA table_info(chat_sessions)")
        sessions_cols = cursor.fetchall()
        print("chat_sessions:")
        for col in sessions_cols:
            print(f"  • {col[1]} - {col[2]}")
        
        cursor.execute("PRAGMA table_info(chat_messages)")
        messages_cols = cursor.fetchall()
        print("\nchat_messages:")
        for col in messages_cols:
            print(f"  • {col[1]} - {col[2]}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        messages_count = cursor.fetchone()[0]
        
        print(f"\n📊 Registros:")
        print(f"  • Sessions: {sessions_count}")
        print(f"  • Messages: {messages_count}")
        
        print("\n🎉 Tabelas corrigidas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_instance_chat_tables()
    if success:
        print("\n✅ Sistema de chat pronto para uso!")
    else:
        print("\n❌ Erro na correção!")
