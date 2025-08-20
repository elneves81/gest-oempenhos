# Novo sistema de API para widgets
from flask import jsonify, request
from flask_login import login_required
from datetime import date, datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, case

from models import db, Contrato, Empenho

# ===== Helpers robustos =====
def _safe_date_col(model, primary_name, fallback_name):
    """
    Retorna a coluna de data com fallback (ex.: data_criacao -> data_empenho).
    """
    return getattr(model, primary_name, None) or getattr(model, fallback_name, None)

def _last_months_labels(n=12):
    hoje = date.today().replace(day=1)
    labels = []
    for i in range(n-1, -1, -1):
        d = (hoje.replace(day=15) - timedelta(days=30*i))  # aproximação mensal
        labels.append(d.strftime('%m/%Y'))
    # remover duplicados caso a aproximação crie repetição (raro)
    dedup, seen = [], set()
    for l in labels:
        if l not in seen:
            dedup.append(l); seen.add(l)
    return dedup[-n:]

def _month_key(dt):
    return dt.strftime('%m/%Y')

def _fmt_money(v):
    return float(v or 0.0)

# ====== API para widgets ======
@relatorios_bp.route("/api/widget-data/<widget_id>")
@login_required
def widget_data(widget_id):
    """
    Devolve JSON específico por widget_id:
      - kpi-empenhos        -> { total, ativos }
      - kpi-financeiro      -> { valor_total, variacao }
      - grafico-evolucao    -> { evolucao: { labels, values } }
      - grafico-pizza       -> { pizza:   { labels, values } }
      - tabela-top-fornecedores -> { fornecedores: [{nome, valor}] }
      - alertas-sistema     -> { alertas: [{tipo, icone, titulo, mensagem}] }
      - calendario-vencimentos -> { vencimentos: [{data, titulo, tipo}] }
    """
    try:
        if widget_id == "kpi-empenhos":
            return jsonify(_data_kpi_empenhos())

        if widget_id == "kpi-financeiro":
            return jsonify(_data_kpi_financeiro())

        if widget_id == "grafico-evolucao":
            return jsonify(_data_grafico_evolucao())

        if widget_id == "grafico-pizza":
            return jsonify(_data_grafico_pizza())

        if widget_id == "tabela-top-fornecedores":
            return jsonify(_data_top_fornecedores())

        if widget_id == "alertas-sistema":
            return jsonify(_data_alertas_sistema())

        if widget_id == "calendario-vencimentos":
            return jsonify(_data_calendario_vencimentos())

        return jsonify({"error": "widget não implementado"}), 404

    except Exception as e:
        # Fallback seguro com estrutura mínima para não quebrar o front
        return jsonify({
            "error": str(e),
            "fallback": True
        }), 200

# ===== Implementações =====

def _data_kpi_empenhos():
    total = db.session.query(func.count(Empenho.id)).scalar() or 0
    # status 'ATIVO' não é típico em empenho; ajuste: considera aprovados/pagos como "ativos"
    ativos = db.session.query(func.count(Empenho.id)).filter(
        func.upper(Empenho.status).in_(["APROVADO", "PAGO"])
    ).scalar() or 0

    return {"total": int(total), "ativos": int(ativos)}

def _data_kpi_financeiro():
    # Total empenhado no mês atual vs mês anterior para % de variação
    col_data = _safe_date_col(Empenho, 'data_criacao', 'data_empenho')
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    # mês anterior
    if inicio_mes.month == 1:
        inicio_mes_ant = inicio_mes.replace(year=inicio_mes.year - 1, month=12)
    else:
        inicio_mes_ant = inicio_mes.replace(month=inicio_mes.month - 1)

    total_mes = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0))\
        .filter(col_data >= inicio_mes).scalar() or 0.0

    total_mes_ant = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0))\
        .filter(col_data >= inicio_mes_ant, col_data < inicio_mes).scalar() or 0.0

    variacao = 0.0
    if total_mes_ant:
        variacao = ((total_mes - total_mes_ant) / total_mes_ant) * 100.0

    # Também devolve o total geral, que é útil pro KPI
    valor_total = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0)).scalar() or 0.0

    return {
        "valor_total": _fmt_money(valor_total),
        "variacao": round(variacao, 1)
    }

def _data_grafico_evolucao():
    """
    Evolução mensal (últimos 12 meses) do valor_empenhado.
    """
    col_data = _safe_date_col(Empenho, 'data_criacao', 'data_empenho')
    labels = _last_months_labels(12)
    # traz últimos 14 meses para garantir cobertura e depois agrega em Python (mais portável)
    dt_limite = date.today() - timedelta(days=430)

    rows = db.session.query(col_data, Empenho.valor_empenhado)\
        .filter(col_data.isnot(None), col_data >= dt_limite)\
        .all()

    agg = defaultdict(float)
    for dt, valor in rows:
        if not dt:
            continue
        key = _month_key(dt)
        agg[key] += float(valor or 0.0)

    values = [round(agg.get(lbl, 0.0), 2) for lbl in labels]

    return {"evolucao": {"labels": labels, "values": values}}

def _data_grafico_pizza():
    """
    Pizza por status de EMPENHO (ajuste conforme sua necessidade).
    """
    # Mapeia status que existirem em banco
    rows = db.session.query(func.upper(Empenho.status), func.count(Empenho.id))\
        .group_by(func.upper(Empenho.status)).all()

    labels, values = [], []
    for status, qtd in rows:
        labels.append(status or "N/D")
        values.append(int(qtd or 0))

    # Fallback se não houver nada
    if not labels:
        labels = ["Sem dados"]
        values = [1]

    return {"pizza": {"labels": labels, "values": values}}

def _data_top_fornecedores():
    """
    Top fornecedores por soma de valor_empenhado (Empenho) ou valor_total (Contrato).
    Tenta primeiro Empenho.fornecedor; se não existir, usa Contrato.fornecedor.
    """
    fornecedores = []

    # Tenta via Empenho
    if hasattr(Empenho, "fornecedor"):
        rows = db.session.query(
            Empenho.fornecedor,
            func.coalesce(func.sum(Empenho.valor_empenhado), 0.0)
        ).group_by(Empenho.fornecedor).order_by(func.sum(Empenho.valor_empenhado).desc()).limit(10).all()

        fornecedores = [{"nome": r[0] or "N/D", "valor": _fmt_money(r[1])} for r in rows if r[0]]
    # Senão tenta via Contrato
    elif hasattr(Contrato, "fornecedor"):
        rows = db.session.query(
            Contrato.fornecedor,
            func.coalesce(func.sum(Contrato.valor_total), 0.0)
        ).group_by(Contrato.fornecedor).order_by(func.sum(Contrato.valor_total).desc()).limit(10).all()

        fornecedores = [{"nome": r[0] or "N/D", "valor": _fmt_money(r[1])} for r in rows if r[0]]

    # Fallback
    if not fornecedores:
        fornecedores = [
            {"nome": "Fornecedor A", "valor": 120000.00},
            {"nome": "Fornecedor B", "valor": 98000.00},
            {"nome": "Fornecedor C", "valor": 75500.50}
        ]

    return {"fornecedores": fornecedores}

def _data_alertas_sistema():
    """
    Alertas com base em contratos próximos do fim e empenhos pendentes.
    """
    alertas = []

    hoje = date.today()
    # Contratos que vencem em <= 30 dias
    if hasattr(Contrato, "data_fim"):
        proximos = Contrato.query.filter(
            Contrato.data_fim.isnot(None),
            Contrato.data_fim >= hoje,
            Contrato.data_fim <= hoje + timedelta(days=30)
        ).count() or 0

        if proximos:
            alertas.append({
                "tipo": "warning",
                "icone": "bi bi-calendar-event",
                "titulo": "Contratos a vencer",
                "mensagem": f"{proximos} contrato(s) vencendo em até 30 dias."
            })

    # Empenhos pendentes
    pendentes = Empenho.query.filter(func.upper(Empenho.status) == "PENDENTE").count() or 0
    if pendentes:
        alertas.append({
            "tipo": "danger",
            "icone": "bi bi-exclamation-triangle",
            "titulo": "Empenhos pendentes",
            "mensagem": f"{pendentes} empenho(s) aguardando aprovação."
        })

    if not alertas:
        alertas = [{
            "tipo": "success",
            "icone": "bi bi-check-circle",
            "titulo": "Tudo certo",
            "mensagem": "Nenhum alerta no momento."
        }]

    return {"alertas": alertas}

def _data_calendario_vencimentos():
    """
    Vencimentos nos próximos 45 dias com base em Contrato.data_fim.
    """
    vencimentos = []
    hoje = date.today()
    if hasattr(Contrato, "data_fim"):
        rows = Contrato.query.filter(
            Contrato.data_fim.isnot(None),
            Contrato.data_fim >= hoje,
            Contrato.data_fim <= hoje + timedelta(days=45)
        ).order_by(Contrato.data_fim.asc()).limit(20).all()

        for c in rows:
            titulo = getattr(c, "objeto", None) or f"Contrato #{c.id}"
            vencimentos.append({
                "data": c.data_fim.isoformat(),
                "titulo": titulo,
                "tipo": "Contrato"
            })

    if not vencimentos:
        # Fallback amigável
        vencimentos = [{
            "data": (hoje + timedelta(days=7)).isoformat(),
            "titulo": "Exemplo: Renovação de contrato",
            "tipo": "Contrato"
        }]

    return {"vencimentos": vencimentos}
