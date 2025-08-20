# routes_contratos.py
from flask import Blueprint, request, jsonify
from models import db
from models import ContratoOtimizado as Contrato
from services.contrato import criar_contrato, aditivo_contrato, empenhar_no_contrato, get_stats_contratos

contr_bp = Blueprint("contr", __name__, url_prefix="/api/contratos")

@contr_bp.get("/")
def list_contratos():
    q = Contrato.query.order_by(Contrato.id.desc())
    rows = q.all()
    return jsonify([{
        "id": c.id, 
        "numero": c.numero, 
        "fornecedor": c.fornecedor, 
        "status": c.status,
        "valor_inicial": float(c.valor_inicial or 0),
        "aditivos_total": float(c.aditivos_total or 0),
        "valor_atualizado": float(c.valor_atualizado or 0),
        "empenhado": float(c.empenhado_contrato or 0),
        "saldo": c.saldo_contrato
    } for c in rows])

@contr_bp.post("/")
def post_contrato():
    try:
        c = criar_contrato(request.json)
        return jsonify({"ok": True, "id": c.id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@contr_bp.post("/<int:cid>/aditivo")
def post_aditivo(cid):
    try:
        v = request.json.get("valor")
        c = aditivo_contrato(cid, v)
        return jsonify({"ok": True, "valor_atualizado": float(c.valor_atualizado)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@contr_bp.post("/<int:cid>/empenhos")
def post_empenho_contrato(cid):
    try:
        emp = empenhar_no_contrato(cid, request.json)
        return jsonify({"ok": True, "empenho_id": emp.id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# stats para seus KPIs
@contr_bp.get("/stats")
def stats_contratos():
    try:
        stats = get_stats_contratos()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"total": 0, "valor_total": 0})

@contr_bp.get("/search")
def search_contratos():
    """Busca contratos para select2"""
    q = request.args.get('q', '')
    query = Contrato.query
    if q:
        query = query.filter(
            db.or_(
                Contrato.numero.contains(q),
                Contrato.fornecedor.contains(q)
            )
        )
    
    results = query.limit(20).all()
    return jsonify({
        "results": [
            {
                "id": c.id,
                "text": f"{c.numero} - {c.fornecedor} (R$ {c.saldo_contrato:,.2f})"
            }
            for c in results
        ]
    })
