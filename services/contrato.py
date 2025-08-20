# services/contrato.py
from models import db
from models import ContratoOtimizado as Contrato, Empenho
from services.orcamento import criar_empenho  # vamos reaproveitar
from datetime import date

def criar_contrato(d):
    c = Contrato(
        numero=d["numero"].strip(),
        fornecedor=d["fornecedor"].strip(),
        objeto=d.get("objeto"),
        data_inicio=d.get("data_inicio"),
        data_fim=d.get("data_fim"),
        valor_inicial=float(d.get("valor_inicial") or 0),
        aditivos_total=float(d.get("aditivos_total") or 0),
        valor_atualizado=float(d.get("valor_inicial") or 0) + float(d.get("aditivos_total") or 0),
        status=d.get("status","VIGENTE"),
        orcamento_id=d.get("orcamento_id")
    )
    db.session.add(c)
    db.session.commit()
    return c

def aditivo_contrato(contrato_id, valor, descricao=None):
    c = db.session.get(Contrato, contrato_id)
    if not c: 
        raise ValueError("Contrato não encontrado.")
    valor = float(valor or 0)
    if valor <= 0: 
        raise ValueError("Valor do aditivo inválido.")

    c.aditivos_total = float(c.aditivos_total or 0) + valor
    c.valor_atualizado = float(c.valor_inicial or 0) + float(c.aditivos_total or 0)
    db.session.commit()
    return c

def empenhar_no_contrato(contrato_id, payload_empenho):
    """
    payload_empenho: {numero, fornecedor, valor, orcamento_id?}
    - valida saldo do contrato
    - cria empenho (services.orcamento), vinculando ao contrato
    - incrementa 'empenhado_contrato'
    """
    c = db.session.get(Contrato, contrato_id)
    if not c: 
        raise ValueError("Contrato não encontrado.")
    valor = float(payload_empenho["valor"])
    if valor > c.saldo_contrato:
        raise ValueError(f"Saldo do contrato insuficiente. Disponível: {c.saldo_contrato:,.2f}")

    # se não enviar orcamento_id, usa o principal do contrato (se houver)
    if not payload_empenho.get("orcamento_id"):
        if not c.orcamento_id:
            raise ValueError("Informe uma linha orçamentária para o empenho.")
        payload_empenho["orcamento_id"] = c.orcamento_id

    # Criar empenho orçamentário (se disponível)
    try:
        emp = criar_empenho(payload_empenho)  # já abate do orçamento
        # vincula ao contrato
        emp.contrato_id = c.id
        c.empenhado_contrato = float(c.empenhado_contrato or 0) + valor
        db.session.commit()
        return emp
    except Exception as e:
        # Se falhar com orçamentário, criar empenho tradicional
        emp = Empenho(
            numero_empenho=payload_empenho["numero"],
            data_empenho=payload_empenho.get("data", date.today()),
            valor_empenhado=valor,
            objeto=f"Empenho do contrato {c.numero}",
            numero_contrato=c.numero,
            fornecedores=payload_empenho["fornecedor"],
            contrato_id=c.id,
            usuario_id=1  # TODO: pegar do contexto atual
        )
        db.session.add(emp)
        c.empenhado_contrato = float(c.empenhado_contrato or 0) + valor
        db.session.commit()
        return emp

def get_stats_contratos():
    """Estatísticas para KPIs"""
    total = Contrato.query.count()
    soma = sum(float(c.valor_atualizado or 0) for c in Contrato.query.all())
    return {"total": total, "valor_total": soma}
