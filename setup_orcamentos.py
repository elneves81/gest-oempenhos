# setup_orcamentos.py
from flask import Blueprint, jsonify
from models import db
from sqlalchemy import text

setup_bp = Blueprint("setup", __name__, url_prefix="/setup")

@setup_bp.get("/orcamentos")
def setup_orc():
    try:
        # cria tabelas se não existem
        from models_orcamento import Orcamento, EmpenhoOrcamentario
        db.create_all()

        # garantir coluna orcamento_id na tabela de empenhos (SQLite às vezes vem sem)
        info = db.session.execute(text("PRAGMA table_info(empenhos_orcamentarios)")).fetchall()
        cols = {r[1] for r in info}
        if 'orcamento_id' not in cols:
            # SQLite não suporta add FK completo fácil; faremos add column simples:
            db.session.execute(text("ALTER TABLE empenhos_orcamentarios ADD COLUMN orcamento_id INTEGER"))
            db.session.commit()

        # Criar dados de exemplo se não existir
        if Orcamento.query.count() == 0:
            criar_dados_exemplo()

        return jsonify({"ok": True, "message": "Setup orçamentário concluído com sucesso!"})
    
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

def criar_dados_exemplo():
    """Cria dados de exemplo para demonstração"""
    from models_orcamento import Orcamento
    
    dados_exemplo = [
        {
            "ano": 2025, "orgao": "Secretaria de Saúde", "unidade": "Hospital Municipal",
            "funcao": "Saúde", "subfuncao": "Assistência Hospitalar", 
            "programa": "Atenção Básica de Saúde", "acao": "Consultas Médicas",
            "fonte_recurso": "Recursos Próprios", "categoria": "SAUDE",
            "dotado": 500000.00, "atualizado": 480000.00
        },
        {
            "ano": 2025, "orgao": "Secretaria de Saúde", "unidade": "UBS Central",
            "funcao": "Saúde", "subfuncao": "Atenção Básica", 
            "programa": "PSF - Programa Saúde da Família", "acao": "Atendimento Ambulatorial",
            "fonte_recurso": "SUS", "categoria": "SAUDE",
            "dotado": 300000.00, "atualizado": 290000.00
        },
        {
            "ano": 2025, "orgao": "Secretaria de Educação", "unidade": "Escola Municipal Central",
            "funcao": "Educação", "subfuncao": "Ensino Fundamental", 
            "programa": "Educação Básica", "acao": "Manutenção do Ensino",
            "fonte_recurso": "FUNDEB", "categoria": "GERAL",
            "dotado": 800000.00, "atualizado": 750000.00
        },
        {
            "ano": 2025, "orgao": "Secretaria de Obras", "unidade": "Departamento de Infraestrutura",
            "funcao": "Urbanismo", "subfuncao": "Infraestrutura Urbana", 
            "programa": "Melhoria da Infraestrutura", "acao": "Pavimentação de Ruas",
            "fonte_recurso": "Recursos Próprios", "categoria": "GERAL",
            "dotado": 1200000.00, "atualizado": 1100000.00
        },
        {
            "ano": 2025, "orgao": "Secretaria de Saúde", "unidade": "Farmácia Municipal",
            "funcao": "Saúde", "subfuncao": "Assistência Farmacêutica", 
            "programa": "Medicamentos Básicos", "acao": "Aquisição de Medicamentos",
            "fonte_recurso": "SUS", "categoria": "SAUDE",
            "dotado": 200000.00, "atualizado": 185000.00
        }
    ]
    
    for dado in dados_exemplo:
        orc = Orcamento(**dado)
        db.session.add(orc)
    
    db.session.commit()
    print("✅ Dados de exemplo criados para orçamentos!")
