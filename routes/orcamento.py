# routes/orcamento.py
from flask import Blueprint, request, jsonify
from models import db
from models_orcamento import Orcamento, EmpenhoOrcamentario
from services.orcamento import criar_empenho, liquidar_empenho, pagar_empenho, get_resumo_orcamento

orc_bp = Blueprint("orc", __name__, url_prefix="/api/orcamento")

@orc_bp.get("/resumo")
def resumo():
    """Resumo orçamentário por ano e categoria"""
    ano = int(request.args.get("ano", 2025))
    cat = request.args.get("categoria")  # SAUDE|GERAL|None
    
    q = Orcamento.query.filter_by(ano=ano)
    if cat: 
        q = q.filter_by(categoria=cat)

    total = {"dotado":0,"atualizado":0,"empenhado":0,"liquidado":0,"pago":0}
    linhas = []
    
    for o in q.all():
        def f(x): return float(x or 0)
        total["dotado"]     += f(o.valor_dotado)
        total["atualizado"] += f(o.valor_atualizado)
        total["empenhado"]  += f(o.empenhado)
        total["liquidado"]  += f(o.liquidado)
        total["pago"]       += f(o.pago)
        
        linhas.append({
            "id": o.id, 
            "orgao": o.orgao, 
            "unidade": o.unidade,
            "fonte": o.fonte, 
            "categoria": o.categoria,
            "dotado": f(o.valor_dotado), 
            "atualizado": f(o.valor_atualizado),
            "empenhado": f(o.empenhado), 
            "liquidado": f(o.liquidado), 
            "pago": f(o.pago),
            "saldo_empenhar": o.saldo_a_empenhar, 
            "saldo_liquidar": o.saldo_a_liquidar,
            "saldo_pagar": o.saldo_a_pagar
        })
    
    return jsonify({"total": total, "linhas": linhas})

@orc_bp.get("/")
def listar_orcamentos():
    """Lista todos os orçamentos com filtros"""
    ano = request.args.get("ano", type=int)
    categoria = request.args.get("categoria")
    orgao = request.args.get("orgao")
    
    q = Orcamento.query
    if ano:
        q = q.filter_by(ano=ano)
    if categoria:
        q = q.filter_by(categoria=categoria)
    if orgao:
        q = q.filter(Orcamento.orgao.ilike(f"%{orgao}%"))
    
    orcamentos = []
    for o in q.all():
        orcamentos.append({
            "id": o.id,
            "ano": o.ano,
            "orgao": o.orgao,
            "unidade": o.unidade,
            "categoria": o.categoria,
            "dotado": float(o.dotado or 0),
            "atualizado": float(o.atualizado or 0),
            "empenhado": float(o.empenhado or 0),
            "liquidado": float(o.liquidado or 0),
            "pago": float(o.pago or 0),
            "saldo_a_empenhar": o.saldo_a_empenhar
        })
    
    return jsonify({"orcamentos": orcamentos})

@orc_bp.post("/empenhos")
def post_empenho():
    """Cria um novo empenho orçamentário"""
    try:
        emp = criar_empenho(request.json)
        return jsonify({"ok": True, "id": emp.id, "numero": emp.numero})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Erro interno do servidor"}), 500

@orc_bp.post("/empenhos/<int:emp_id>/liquidar")
def post_liquidar(emp_id):
    """Liquida um empenho orçamentário"""
    try:
        emp = liquidar_empenho(emp_id, request.json.get("valor"))
        return jsonify({"ok": True, "status": emp.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Erro interno do servidor"}), 500

@orc_bp.post("/empenhos/<int:emp_id>/pagar")
def post_pagar(emp_id):
    """Efetua o pagamento de um empenho orçamentário"""
    try:
        emp = pagar_empenho(emp_id, request.json.get("valor"))
        return jsonify({"ok": True, "status": emp.status})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Erro interno do servidor"}), 500

@orc_bp.get("/saldos/<int:orcamento_id>")
def get_saldos(orcamento_id):
    """Consulta saldos de um orçamento específico"""
    try:
        orc = Orcamento.query.get_or_404(orcamento_id)
        saldos = {
            "dotado": float(orc.valor_dotado or 0),
            "atualizado": float(orc.valor_atualizado or 0),
            "empenhado": float(orc.empenhado or 0),
            "liquidado": float(orc.liquidado or 0),
            "pago": float(orc.pago or 0),
            "saldo_a_empenhar": orc.saldo_a_empenhar,
            "saldo_a_liquidar": orc.saldo_a_liquidar,
            "saldo_a_pagar": orc.saldo_a_pagar
        }
        return jsonify(saldos)
    except Exception as e:
        return jsonify({"error": "Erro interno do servidor"}), 500

@orc_bp.get("/empenhos")
def listar_empenhos():
    """Lista empenhos orçamentários com filtros"""
    orcamento_id = request.args.get("orcamento_id", type=int)
    status = request.args.get("status")
    
    q = EmpenhoOrcamentario.query
    if orcamento_id:
        q = q.filter_by(orcamento_id=orcamento_id)
    if status:
        q = q.filter_by(status=status)
    
    empenhos = []
    for e in q.all():
        empenhos.append({
            "id": e.id,
            "numero": e.numero,
            "data": e.data.isoformat() if e.data else None,
            "fornecedor": e.fornecedor,
            "valor": float(e.valor),
            "status": e.status,
            "orcamento_id": e.orcamento_id,
            "orgao": e.orcamento.orgao if e.orcamento else None
        })
    
    return jsonify({"empenhos": empenhos})
