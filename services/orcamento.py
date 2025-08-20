# services/orcamento.py
from models import db
from models_orcamento import Orcamento, EmpenhoOrcamentario
from datetime import date

def _round(v): return round(float(v), 2)

def criar_empenho(d):
    """Cria um novo empenho orçamentário"""
    orc = db.session.get(Orcamento, d["orcamento_id"])
    if not orc: 
        raise ValueError("Orçamento não encontrado.")
    
    valor = _round(d["valor"])
    if valor > orc.saldo_a_empenhar:
        raise ValueError(f"Saldo insuficiente: disponível R$ {orc.saldo_a_empenhar:,.2f}")
    
    emp = EmpenhoOrcamentario(
        numero=d["numero"], 
        fornecedor=d["fornecedor"],
        descricao=d.get("descricao", ""),
        valor_empenhado=valor, 
        data=d.get("data", date.today()),
        orcamento_id=orc.id, 
        status="EMPENHADO"
    )
    db.session.add(emp)
    orc.empenhado = _round((orc.empenhado or 0) + valor)
    db.session.commit()
    return emp

def liquidar_empenho(emp_id, valor=None):
    """Liquida um empenho orçamentário"""
    emp = db.session.get(EmpenhoOrcamentario, emp_id)
    if not emp:
        raise ValueError("Empenho não encontrado.")
    
    orc = emp.orcamento
    v = _round(valor or emp.valor_empenhado)
    
    if v > orc.saldo_a_liquidar: 
        raise ValueError(f"Saldo a liquidar insuficiente: disponível R$ {orc.saldo_a_liquidar:,.2f}")
    
    emp.valor_liquidado = v
    emp.status = "LIQUIDADO"
    orc.liquidado = _round((orc.liquidado or 0) + v)
    db.session.commit()
    return emp

def pagar_empenho(emp_id, valor=None):
    """Efetua o pagamento de um empenho orçamentário"""
    emp = db.session.get(EmpenhoOrcamentario, emp_id)
    if not emp:
        raise ValueError("Empenho não encontrado.")
    
    orc = emp.orcamento
    v = _round(valor or emp.valor_empenhado)
    
    if v > orc.saldo_a_pagar: 
        raise ValueError(f"Saldo a pagar insuficiente: disponível R$ {orc.saldo_a_pagar:,.2f}")
    
    emp.valor_pago = v
    emp.status = "PAGO"
    orc.pago = _round((orc.pago or 0) + v)
    db.session.commit()
    return emp

def get_resumo_orcamento(ano=2025, categoria=None):
    """Retorna resumo orçamentário por ano e categoria"""
    q = Orcamento.query.filter_by(ano=ano)
    if categoria: 
        q = q.filter_by(categoria=categoria)

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
    
    return {"total": total, "linhas": linhas}

class OrcamentoService:
    """Service class para operações orçamentárias"""
    
    @staticmethod
    def gerar_resumo(ano=None, categoria=None):
        """Gera resumo orçamentário consolidado"""
        return get_resumo_orcamento(ano or 2025, categoria)
