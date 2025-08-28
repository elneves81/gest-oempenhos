# normalize_chat_schema.py
from app import app, db
from sqlalchemy import text

def has_col(tbl, col):
    rows = db.session.execute(text(f"PRAGMA table_info({tbl})")).mappings().all()
    return any(r["name"] == col for r in rows)

def has_index(name):
    row = db.session.execute(text(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=:n"
    ), {"n": name}).scalar()
    return bool(row)

def table_exists(name):
    row = db.session.execute(text(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"
    ), {"n": name}).scalar()
    return bool(row)

with app.app_context():
    print("DB:", db.engine.url.database)

    # Verificar se chat_rooms existe, senão criar
    if not table_exists("chat_rooms"):
        print("Criando tabela chat_rooms...")
        db.session.execute(text("""
            CREATE TABLE chat_rooms (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                kind VARCHAR(20) NOT NULL DEFAULT 'group',
                created_by INTEGER,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                dm_key VARCHAR(64) UNIQUE,
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        """))

    # chat_rooms - adicionar colunas se não existirem
    if not has_col("chat_rooms", "kind"):
        print("Adicionando coluna 'kind' à tabela chat_rooms...")
        db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN kind TEXT NOT NULL DEFAULT 'group'"))

    if not has_col("chat_rooms", "dm_key"):
        print("Adicionando coluna 'dm_key' à tabela chat_rooms...")
        db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN dm_key TEXT"))

    if not has_index("uq_chat_rooms_dm_key"):
        print("Criando índice único para dm_key...")
        # índice único só quando dm_key não é NULL (grupos não preenchem)
        db.session.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_chat_rooms_dm_key ON chat_rooms(dm_key) WHERE dm_key IS NOT NULL"
        ))

    if not has_index("ix_chat_rooms_kind"):
        print("Criando índice para kind...")
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_rooms_kind ON chat_rooms(kind)"))

    # Verificar se chat_members existe, senão criar
    if not table_exists("chat_members"):
        print("Criando tabela chat_members...")
        db.session.execute(text("""
            CREATE TABLE chat_members (
                id INTEGER PRIMARY KEY,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(room_id) REFERENCES chat_rooms(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))

    # chat_members: unique (room_id, user_id)
    if not has_index("uq_room_user"):
        print("Criando índice único para room_id, user_id...")
        db.session.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_room_user ON chat_members(room_id, user_id)"
        ))

    # Verificar se chat_room_messages existe, senão criar
    if not table_exists("chat_room_messages"):
        print("Criando tabela chat_room_messages...")
        db.session.execute(text("""
            CREATE TABLE chat_room_messages (
                id INTEGER PRIMARY KEY,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT,
                text TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY(room_id) REFERENCES chat_rooms(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))

    # chat_room_messages: garantir coluna 'content' e migrar dados de 'text'
    if table_exists("chat_room_messages"):
        if not has_col("chat_room_messages", "content"):
            print("Adicionando coluna 'content' à tabela chat_room_messages...")
            db.session.execute(text("ALTER TABLE chat_room_messages ADD COLUMN content TEXT"))
            db.session.execute(text("UPDATE chat_room_messages SET content = text WHERE content IS NULL AND text IS NOT NULL"))

        if not has_col("chat_room_messages", "deleted"):
            print("Adicionando coluna 'deleted' à tabela chat_room_messages...")
            db.session.execute(text("ALTER TABLE chat_room_messages ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT 0"))

    # saneamento de dm_key: prefixo "dm:" quando for DM (mais seguro)
    if table_exists("chat_rooms") and table_exists("chat_members"):
        print("Atualizando dm_key para DMs...")
        try:
            # Primeiro, limpar duplicatas existentes
            db.session.execute(text("UPDATE chat_rooms SET dm_key = NULL WHERE kind='dm' AND dm_key IS NOT NULL"))
            
            # Depois, regenerar de forma segura
            db.session.execute(text("""
                UPDATE chat_rooms
                SET dm_key = 'dm:' || 
                            CASE WHEN created_by < (SELECT MIN(user_id) FROM chat_members WHERE room_id=chat_rooms.id)
                                 THEN created_by || ':' || (SELECT MIN(user_id) FROM chat_members WHERE room_id=chat_rooms.id)
                                 ELSE (SELECT MIN(user_id) FROM chat_members WHERE room_id=chat_rooms.id) || ':' || created_by
                            END
                WHERE kind='dm' AND dm_key IS NULL AND created_by IS NOT NULL
                  AND EXISTS (SELECT 1 FROM chat_members WHERE room_id=chat_rooms.id)
            """))
        except Exception as e:
            print(f"Aviso: Erro ao atualizar dm_key: {e}")
            # Continuar mesmo com erro

    # Verificar se as tabelas de Chat IA existem
    if not table_exists("chat_messages"):
        print("Criando tabela chat_messages (IA)...")
        db.session.execute(text("""
            CREATE TABLE chat_messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(100) NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages(session_id)"))

    if not table_exists("chat_sessions"):
        print("Criando tabela chat_sessions (IA)...")
        db.session.execute(text("""
            CREATE TABLE chat_sessions (
                id INTEGER PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL DEFAULT 'Nova Conversa',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_message_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))

    db.session.commit()
    print("OK: schema normalizado com sucesso!")
