# hotfix_chat_rooms_kind.py
from app import app, db
from sqlalchemy import text

def col_exists(table, col):
    rows = db.session.execute(text(f"PRAGMA table_info({table})")).mappings().all()
    return any(r["name"] == col for r in rows)

with app.app_context():
    print("DB:", db.engine.url.database)
    # tabela existe?
    exists = db.session.execute(text(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='chat_rooms'"
    )).scalar()
    if not exists:
        raise SystemExit("ERRO: tabela chat_rooms não existe nesse DB.")

    # adiciona colunas que faltam
    if not col_exists("chat_rooms", "kind"):
        print("Adicionando chat_rooms.kind ...")
        db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN kind TEXT NOT NULL DEFAULT 'group'"))

    if not col_exists("chat_rooms", "dm_key"):
        print("Adicionando chat_rooms.dm_key ...")
        db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN dm_key TEXT"))

    db.session.commit()

    cols = db.session.execute(text("PRAGMA table_info(chat_rooms)")).mappings().all()
    print("Colunas chat_rooms:", [c["name"] for c in cols])
    print("OK.")
