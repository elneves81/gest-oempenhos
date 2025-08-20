# routes_orcamento.py
from flask import Blueprint, request, jsonify
from app import db
from models_orcamento import Orcamento, EmpenhoOrcamentario
from services.orcamento import criar_empenho, liquidar_empenho, pagar_empenho, get_resumo_orcamento

orc_bp = Blueprint("orc", __name__, url_prefix="/api/orcamento")

@orc_bp.get("/resumo")
def resumo():
    """Retorna resumo orçamentário filtrado por ano e categoria"""
    try:
        ano = int(request.args.get("ano", 2025))
        categoria = request.args.get("categoria")  # SAUDE|GERAL|None
        
        dados = get_resumo_orcamento(ano, categoria)
        return jsonify(dados)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@orc_bp.get("/orgaos")
def get_orgaos():
    """Lista todos os órgãos disponíveis"""
    try:
        ano = int(request.args.get("ano", 2025))
        orgaos = db.session.query(Orcamento.orgao).filter_by(ano=ano).distinct().all()
        return jsonify([o[0] for o in orgaos])
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@orc_bp.get("/categorias")
def get_categorias():
    """Lista todas as categorias disponíveis"""
    return jsonify(["GERAL", "SAUDE"])

@orc_bp.post("/empenhos")
def post_empenho():
    """Cria um novo empenho orçamentário"""
    try:
        dados = request.json
        emp = criar_empenho(dados)
        return jsonify({
            "ok": True, 
            "id": emp.id,
            "numero": emp.numero,
            "valor": float(emp.valor),
            "status": emp.status,
            "message": "Empenho criado com sucesso!"
        })
    
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Erro interno: {str(e)}"}), 500

@orc_bp.post("/empenhos/<int:emp_id>/liquidar")
def post_liquidar(emp_id):
    """Liquida um empenho orçamentário"""
    try:
        valor = request.json.get("valor") if request.json else None
        emp = liquidar_empenho(emp_id, valor)
        return jsonify({
            "ok": True, 
            "id": emp.id,
            "status": emp.status,
            "message": "Empenho liquidado com sucesso!"
        })
    
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Erro interno: {str(e)}"}), 500

@orc_bp.post("/empenhos/<int:emp_id>/pagar")
def post_pagar(emp_id):
    """Efetua o pagamento de um empenho orçamentário"""
    try:
        valor = request.json.get("valor") if request.json else None
        emp = pagar_empenho(emp_id, valor)
        return jsonify({
            "ok": True, 
            "id": emp.id,
            "status": emp.status,
            "message": "Empenho pago com sucesso!"
        })
    
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"Erro interno: {str(e)}"}), 500

@orc_bp.get("/empenhos")
def get_empenhos():
    """Lista empenhos orçamentários com filtros"""
    try:
        ano = int(request.args.get("ano", 2025))
        categoria = request.args.get("categoria")
        status = request.args.get("status")
        
        # Join com orçamento para filtrar por ano/categoria
        q = db.session.query(EmpenhoOrcamentario).join(Orcamento).filter(Orcamento.ano == ano)
        
        if categoria:
            q = q.filter(Orcamento.categoria == categoria)
        
        if status:
            q = q.filter(EmpenhoOrcamentario.status == status)
        
        empenhos = q.limit(100).all()  # Limitar resultados
        
        dados = []
        for emp in empenhos:
            dados.append({
                "id": emp.id,
                "numero": emp.numero,
                "fornecedor": emp.fornecedor,
                "valor": float(emp.valor),
                "data": emp.data.isoformat(),
                "status": emp.status,
                "orcamento": {
                    "id": emp.orcamento.id,
                    "orgao": emp.orcamento.orgao,
                    "categoria": emp.orcamento.categoria
                }
            })
        
        return jsonify({"empenhos": dados, "total": len(dados)})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
