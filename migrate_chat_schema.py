# migrate_chat_schema.py
from app import app, db
from sqlalchemy import text
from models_chat import ChatSession, ChatMessage
import uuid

with app.app_context():
    # 1) Adicionar coluna session_id se não existir
    cols = [r[1] for r in db.session.execute(text("PRAGMA table_info(chat_sessions)")).fetchall()]
    if "session_id" not in cols:
        db.session.execute(text("ALTER TABLE chat_sessions ADD COLUMN session_id VARCHAR(100)"))
        db.session.commit()
        print("✅ Coluna session_id adicionada em chat_sessions")

    # 2) Popular session_id vazio
    sessions = ChatSession.query.filter((ChatSession.session_id.is_(None)) | (ChatSession.session_id == '')).all()
    for s in sessions:
        s.session_id = str(uuid.uuid4())
    db.session.commit()
    print(f"✅ session_id populado em {len(sessions)} sessão(ões)")

    # 3) (Opcional) garantir índices básicos
    db.session.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)"
    ))
    db.session.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_chat_sessions_last_message_at ON chat_sessions (last_message_at)"
    ))
    db.session.commit()
    print("✅ Índices criados/garantidos")

    # 4) Conferir também chat_messages.session_id
    cols_msg = [r[1] for r in db.session.execute(text("PRAGMA table_info(chat_messages)")).fetchall()]
    if "session_id" not in cols_msg:
        db.session.execute(text("ALTER TABLE chat_messages ADD COLUMN session_id VARCHAR(100)"))
        db.session.commit()
        print("✅ Coluna session_id adicionada em chat_messages")

    # (Opcional) index para busca por sessão
    db.session.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages (session_id)"
    ))
    db.session.commit()
    print("✅ Índice em chat_messages.session_id criado/garantido")

print("🎉 Migração concluída.")
