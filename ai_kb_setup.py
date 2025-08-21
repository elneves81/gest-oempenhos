# ai_kb_setup.py
from sqlalchemy import text
from models import db

def ensure_ai_kb_schema():
    """Configura o esquema completo da Base de Conhecimento da IA"""
    print("🧠 Configurando Base de Conhecimento da IA...")
    
    with db.engine.begin() as conn:
        # Tabela principal
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_kb_entries (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            answer   TEXT NOT NULL,
            keywords TEXT,                -- lista separada por vírgula
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """))

        # Links (para relacionar perguntas similares/duplicadas/seguimento)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ai_kb_links (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation  TEXT NOT NULL DEFAULT 'related', -- 'related' | 'duplicate' | 'followup'
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_id, target_id, relation)
        );
        """))

        # FTS5 (espelha question+answer+keywords)
        # Obs.: usar 'unicode61' p/ acentos e português
        conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS ai_kb_entries_fts
        USING fts5(question, answer, keywords, content='ai_kb_entries', content_rowid='id', tokenize='unicode61');
        """))

        # Popular FTS se estiver vazia
        conn.execute(text("""
        INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
        SELECT id, question, answer, IFNULL(keywords,'')
        FROM ai_kb_entries
        WHERE NOT EXISTS (SELECT 1 FROM ai_kb_entries_fts LIMIT 1);
        """))

        # Triggers de sincronização
        conn.execute(text("DROP TRIGGER IF EXISTS ai_kb_entries_ai;"))
        conn.execute(text("""
        CREATE TRIGGER ai_kb_entries_ai AFTER INSERT ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
            VALUES (new.id, new.question, new.answer, IFNULL(new.keywords,''));
        END;
        """))

        conn.execute(text("DROP TRIGGER IF EXISTS ai_kb_entries_ad;"))
        conn.execute(text("""
        CREATE TRIGGER ai_kb_entries_ad AFTER DELETE ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(ai_kb_entries_fts, rowid, question, answer, keywords)
            VALUES ('delete', old.id, old.question, old.answer, old.keywords);
        END;
        """))

        conn.execute(text("DROP TRIGGER IF EXISTS ai_kb_entries_au;"))
        conn.execute(text("""
        CREATE TRIGGER ai_kb_entries_au AFTER UPDATE ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(ai_kb_entries_fts, rowid, question, answer, keywords)
            VALUES ('delete', old.id, old.question, old.answer, old.keywords);
            INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
            VALUES (new.id, new.question, new.answer, IFNULL(new.keywords,''));
        END;
        """))
    
    print("✅ Base de Conhecimento configurada com FTS5!")

def populate_initial_kb():
    """Popula a KB com dados iniciais do sistema de empenhos"""
    print("📝 Populando KB com dados iniciais...")
    
    initial_entries = [
        {
            "question": "Como criar um novo empenho?",
            "answer": "Para criar um novo empenho, acesse o menu 'Empenhos' → 'Novo Empenho'. Preencha os campos obrigatórios: número do empenho, favorecido, valor empenhado, data do empenho e selecione o status. Clique em 'Salvar' para finalizar.",
            "keywords": "novo empenho, criar empenho, cadastrar empenho, adicionar empenho"
        },
        {
            "question": "Como consultar empenhos existentes?",
            "answer": "Acesse o menu 'Empenhos' para ver a lista completa. Use os filtros disponíveis para buscar por período, favorecido, status ou valor. Você também pode usar a busca rápida no topo da página.",
            "keywords": "consultar empenhos, buscar empenhos, filtrar empenhos, listar empenhos"
        },
        {
            "question": "Como criar um novo contrato?",
            "answer": "Vá em 'Contratos' → 'Novo Contrato'. Preencha os dados: número do contrato, fornecedor, objeto, valor total, datas de início e fim, e status. Certifique-se de que todas as informações estão corretas antes de salvar.",
            "keywords": "novo contrato, criar contrato, cadastrar contrato, adicionar contrato"
        },
        {
            "question": "O que significam os status dos empenhos?",
            "answer": "Os status são: PENDENTE (aguardando aprovação), APROVADO (aprovado para pagamento), PAGO (pagamento realizado), REJEITADO (rejeitado por algum motivo). O status pode ser alterado na edição do empenho.",
            "keywords": "status empenho, pendente, aprovado, pago, rejeitado"
        },
        {
            "question": "Como gerar relatórios?",
            "answer": "Acesse o menu 'Relatórios' onde você encontra várias opções: relatórios por período, por fornecedor, resumos financeiros e dashboards interativos. Você pode exportar os dados em Excel ou PDF.",
            "keywords": "relatórios, exportar, excel, pdf, dashboard, resumo financeiro"
        },
        {
            "question": "Como usar o painel principal?",
            "answer": "O painel principal oferece uma visão geral do sistema com widgets personalizáveis. Clique em 'Adicionar Widget' para escolher KPIs, gráficos ou tabelas. Você pode arrastar, redimensionar e remover widgets conforme sua necessidade.",
            "keywords": "painel, dashboard, widgets, kpi, gráficos, personalizar"
        },
        {
            "question": "Como gerenciar usuários do sistema?",
            "answer": "No menu 'Usuários', administradores podem criar novos usuários, editar permissões e desativar contas. Cada usuário tem login e senha únicos, e diferentes níveis de acesso ao sistema.",
            "keywords": "usuários, gerenciar usuários, permissões, admin, login, senha"
        }
    ]
    
    try:
        for entry in initial_entries:
            db.session.execute(text("""
                INSERT OR IGNORE INTO ai_kb_entries(question, answer, keywords, is_active)
                VALUES (:q, :a, :k, 1)
            """), {
                "q": entry["question"],
                "a": entry["answer"], 
                "k": entry["keywords"]
            })
        
        db.session.commit()
        print("✅ KB populada com dados iniciais!")
        
    except Exception as e:
        print(f"⚠️ Erro ao popular KB: {e}")
        db.session.rollback()
