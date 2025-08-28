#!/usr/bin/env python3
# setup_ai_kb_simple.py
"""
Script simples para configurar as tabelas da Base de Conhecimento IA
"""

import sqlite3
import os

# Caminho do banco de dados
DB_PATH = "empenhos.db"

def setup_ai_kb_tables():
    """Criar tabelas da Base de Conhecimento IA"""
    print("🧠 Configurando Base de Conhecimento da IA...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Criar tabela principal de entradas
        print("📝 Criando tabela ai_kb_entries...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_kb_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Criar tabela de links entre entradas
        print("🔗 Criando tabela ai_kb_links...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_kb_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation TEXT DEFAULT 'related',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES ai_kb_entries(id),
            FOREIGN KEY (target_id) REFERENCES ai_kb_entries(id),
            UNIQUE(source_id, target_id, relation)
        )
        """)
        
        # Criar tabela FTS5 para busca
        print("🔍 Criando tabela FTS5 para busca...")
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS ai_kb_entries_fts 
        USING fts5(question, answer, keywords, content='ai_kb_entries', content_rowid='id', tokenize='unicode61')
        """)
        
        # Inserir dados iniciais se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) FROM ai_kb_entries")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📚 Inserindo dados iniciais...")
            initial_data = [
                ("Como criar um empenho?", "Para criar um empenho, acesse o menu Empenhos > Novo Empenho e preencha os campos obrigatórios.", "empenho criar novo"),
                ("Como consultar contratos?", "Para consultar contratos, acesse o menu Contratos e use os filtros disponíveis para encontrar o contrato desejado.", "contrato consultar buscar"),
                ("Como gerar relatórios?", "Para gerar relatórios, acesse o menu Relatórios e escolha o tipo de relatório desejado. Configure os filtros e clique em Gerar.", "relatorio gerar exportar"),
                ("Como usar o chat IA?", "O chat IA está disponível no menu lateral. Você pode fazer perguntas sobre o sistema e receber respostas automáticas.", "chat ia ajuda"),
                ("Como gerenciar usuários?", "Apenas administradores podem gerenciar usuários. Acesse o menu Usuários para criar, editar ou desativar contas.", "usuario admin gerenciar")
            ]
            
            for question, answer, keywords in initial_data:
                cursor.execute("""
                INSERT INTO ai_kb_entries (question, answer, keywords) 
                VALUES (?, ?, ?)
                """, (question, answer, keywords))
        
        # Sincronizar dados com FTS5
        print("🔄 Sincronizando dados com FTS5...")
        cursor.execute("""
        INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
        SELECT id, question, answer, IFNULL(keywords,'')
        FROM ai_kb_entries
        WHERE NOT EXISTS (SELECT 1 FROM ai_kb_entries_fts WHERE rowid = ai_kb_entries.id)
        """)
        
        # Criar triggers para manter FTS5 sincronizado
        print("⚡ Criando triggers de sincronização...")
        
        # Trigger para INSERT
        cursor.execute("DROP TRIGGER IF EXISTS ai_kb_entries_ai")
        cursor.execute("""
        CREATE TRIGGER ai_kb_entries_ai AFTER INSERT ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
            VALUES (new.id, new.question, new.answer, IFNULL(new.keywords,''));
        END
        """)
        
        # Trigger para DELETE
        cursor.execute("DROP TRIGGER IF EXISTS ai_kb_entries_ad")
        cursor.execute("""
        CREATE TRIGGER ai_kb_entries_ad AFTER DELETE ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(ai_kb_entries_fts, rowid, question, answer, keywords)
            VALUES ('delete', old.id, old.question, old.answer, old.keywords);
        END
        """)
        
        # Trigger para UPDATE
        cursor.execute("DROP TRIGGER IF EXISTS ai_kb_entries_au")
        cursor.execute("""
        CREATE TRIGGER ai_kb_entries_au AFTER UPDATE ON ai_kb_entries BEGIN
            INSERT INTO ai_kb_entries_fts(ai_kb_entries_fts, rowid, question, answer, keywords)
            VALUES ('delete', old.id, old.question, old.answer, old.keywords);
            INSERT INTO ai_kb_entries_fts(rowid, question, answer, keywords)
            VALUES (new.id, new.question, new.answer, IFNULL(new.keywords,''));
        END
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Base de Conhecimento IA configurada com sucesso!")
        print(f"📊 Total de entradas: {count if count > 0 else len(initial_data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Base de Conhecimento: {e}")
        return False

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        setup_ai_kb_tables()
    else:
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        print("Execute o sistema principal primeiro para criar o banco.")
