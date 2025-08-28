#!/usr/bin/env python3
"""
Script para criar/atualizar as tabelas do Chat MSN Style
"""

import sys
import os

# Adicionar o diretório atual ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar usando o arquivo app.py diretamente
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", os.path.join(current_dir, "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
db = app_module.db
from models_chat_msn import ChatRoomOffline, ChatMemberOffline, ChatRoomMessageOffline, ChatAttachment
from sqlalchemy import text

def create_chat_msn_tables():
    """Cria as tabelas necessárias para o Chat MSN Style"""
    print("🔄 Criando/atualizando tabelas do Chat MSN...")
    
    with app.app_context():
        try:
            # Criar todas as tabelas se não existirem
            db.create_all()
            
            # Verificar e adicionar colunas que podem estar faltando
            
            # 1. Verificar message_type na tabela de mensagens
            cols = db.session.execute(text("PRAGMA table_info(chat_room_messages)")).mappings().all()
            col_names = [c["name"] for c in cols]
            
            if "message_type" not in col_names:
                print("   Adicionando coluna message_type...")
                db.session.execute(text("ALTER TABLE chat_room_messages ADD COLUMN message_type TEXT DEFAULT 'text'"))
            
            # 2. Criar tabela de anexos se não existir
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES chat_room_messages (id) ON DELETE CASCADE
                )
            """))
            
            # 3. Criar índices para performance
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_room_created ON chat_room_messages(room_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_chat_attachments_message ON chat_attachments(message_id)",
                "CREATE INDEX IF NOT EXISTS idx_chat_members_room_user ON chat_members(room_id, user_id)"
            ]
            
            for idx_sql in indices:
                try:
                    db.session.execute(text(idx_sql))
                except Exception as e:
                    print(f"   Aviso: Índice já existe ou erro: {e}")
            
            db.session.commit()
            print("✅ Tabelas do Chat MSN criadas/atualizadas com sucesso!")
            
            # Verificar tabelas criadas
            tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            chat_tables = [t[0] for t in tables if 'chat' in t[0]]
            print(f"📊 Tabelas do chat encontradas: {', '.join(chat_tables)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            db.session.rollback()
            return False

def create_initial_data():
    """Cria dados iniciais para o chat"""
    print("🔄 Criando dados iniciais...")
    
    with app.app_context():
        try:
            # Criar sala geral se não existir
            from models import User
            
            geral_room = ChatRoomOffline.query.filter_by(name='Chat Geral', kind='group').first()
            if not geral_room:
                # Buscar primeiro admin/usuário para ser criador
                admin_user = User.query.filter_by(is_admin=True).first()
                if not admin_user:
                    admin_user = User.query.first()
                
                if admin_user:
                    geral_room = ChatRoomOffline(
                        name='Chat Geral',
                        kind='group',
                        created_by=admin_user.id
                    )
                    db.session.add(geral_room)
                    db.session.commit()
                    print("✅ Sala 'Chat Geral' criada!")
                else:
                    print("⚠️ Nenhum usuário encontrado para criar sala inicial")
            else:
                print("✅ Sala 'Chat Geral' já existe!")
                
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar dados iniciais: {e}")
            db.session.rollback()
            return False

def main():
    """Função principal"""
    print("🚀 Configurando Chat MSN Style...")
    print("=" * 50)
    
    if create_chat_msn_tables():
        create_initial_data()
        print("\n🎉 Chat MSN Style configurado com sucesso!")
        print("🔗 Acesse: http://localhost:5001/chat-msn/")
    else:
        print("\n💥 Falha na configuração!")
        sys.exit(1)

if __name__ == "__main__":
    main()
