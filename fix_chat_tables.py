#!/usr/bin/env python3
"""
Script para corrigir a estrutura das tabelas de chat
"""

import sqlite3
import uuid
from datetime import datetime

def fix_chat_tables():
    conn = sqlite3.connect('empenhos.db')
    cursor = conn.cursor()
    
    try:
        print("🔧 Corrigindo estrutura das tabelas de chat...")
        
        # Backup dos dados existentes
        print("📋 Fazendo backup dos dados existentes...")
        
        # Backup chat_sessions
        cursor.execute("SELECT * FROM chat_sessions")
        sessions_backup = cursor.fetchall()
        print(f"   • chat_sessions: {len(sessions_backup)} registros salvos")
        
        # Backup chat_messages  
        cursor.execute("SELECT * FROM chat_messages")
        messages_backup = cursor.fetchall()
        print(f"   • chat_messages: {len(messages_backup)} registros salvos")
        
        # Remover tabelas antigas
        print("🗑️ Removendo tabelas antigas...")
        cursor.execute("DROP TABLE IF EXISTS chat_sessions")
        cursor.execute("DROP TABLE IF EXISTS chat_messages")
        
        # Criar nova estrutura chat_sessions
        print("🔨 Criando nova estrutura chat_sessions...")
        cursor.execute("""
            CREATE TABLE chat_sessions (
                id INTEGER PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) DEFAULT 'Nova Conversa' NOT NULL,
                created_at DATETIME NOT NULL,
                last_message_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Criar nova estrutura chat_messages
        print("🔨 Criando nova estrutura chat_messages...")
        cursor.execute("""
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                timestamp DATETIME NOT NULL,
                session_id VARCHAR(100) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Criar índices
        print("📊 Criando índices...")
        cursor.execute("CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id)")
        cursor.execute("CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id)")
        cursor.execute("CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id)")
        
        # Restaurar dados com nova estrutura
        print("📥 Restaurando dados com nova estrutura...")
        
        # Mapear sessões antigas para novas
        session_mapping = {}
        
        for session in sessions_backup:
            old_id, user_id, title, created_at, updated_at = session
            
            # Gerar novo session_id
            new_session_id = str(uuid.uuid4())
            session_mapping[old_id] = new_session_id
            
            # Usar timestamp atual se não existir
            if not created_at:
                created_at = datetime.utcnow().isoformat()
            if not updated_at:
                updated_at = created_at
                
            cursor.execute("""
                INSERT INTO chat_sessions (session_id, user_id, title, created_at, last_message_at)
                VALUES (?, ?, ?, ?, ?)
            """, (new_session_id, user_id, title or 'Nova Conversa', created_at, updated_at))
        
        print(f"   • {len(sessions_backup)} sessões restauradas")
        
        # Restaurar mensagens
        for message in messages_backup:
            msg_id, user_id, msg_text, response, timestamp, session_id = message
            
            # Usar timestamp atual se não existir
            if not timestamp:
                timestamp = datetime.utcnow().isoformat()
            
            # Mapear session_id se necessário
            if session_id in session_mapping:
                session_id = session_mapping[session_id]
            elif not session_id:
                # Criar nova sessão se não existir
                session_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO chat_sessions (session_id, user_id, title, created_at, last_message_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, user_id, 'Nova Conversa', timestamp, timestamp))
            
            cursor.execute("""
                INSERT INTO chat_messages (user_id, message, response, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, msg_text, response, timestamp, session_id))
        
        print(f"   • {len(messages_backup)} mensagens restauradas")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar estrutura final
        print("\n✅ Verificando estrutura final...")
        
        cursor.execute('PRAGMA table_info(chat_sessions)')
        sessions_cols = cursor.fetchall()
        print("📋 chat_sessions:")
        for col in sessions_cols:
            print(f"   • {col[1]} - {col[2]}")
        
        cursor.execute('PRAGMA table_info(chat_messages)')
        messages_cols = cursor.fetchall()
        print("\n📋 chat_messages:")
        for col in messages_cols:
            print(f"   • {col[1]} - {col[2]}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        messages_count = cursor.fetchone()[0]
        
        print(f"\n📊 Dados finais:")
        print(f"   • Sessions: {sessions_count}")
        print(f"   • Messages: {messages_count}")
        
        print("\n🎉 Estrutura das tabelas de chat corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir tabelas: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_chat_tables()
    if success:
        print("\n✅ Script executado com sucesso!")
        print("🚀 O sistema de chat agora está pronto para uso!")
    else:
        print("\n❌ Erro na execução do script!")
