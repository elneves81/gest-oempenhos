# routes_contr_ui.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models import ContratoOtimizado as Contrato
from services.contrato import criar_contrato, aditivo_contrato, empenhar_no_contrato
from datetime import datetime

ui_contr = Blueprint("ui_contr", __name__)

@ui_contr.get("/contratos/")
def contr_list():
    contratos = Contrato.query.order_by(Contrato.id.desc()).all()
    return render_template("contr_list.html", contratos=contratos)

@ui_contr.get("/contratos/novo")
def contr_new():
    return render_template("contr_form.html", c=None)

@ui_contr.post("/contratos/novo")
def contr_create():
    try:
        f = request.form
        # Conversão de datas
        data_inicio = None
        data_fim = None
        if f.get("data_inicio"):
            data_inicio = datetime.strptime(f["data_inicio"], "%Y-%m-%d").date()
        if f.get("data_fim"):
            data_fim = datetime.strptime(f["data_fim"], "%Y-%m-%d").date()
            
        payload = dict(
            numero=f["numero"], 
            fornecedor=f["fornecedor"], 
            objeto=f.get("objeto"),
            valor_inicial=f.get("valor_inicial") or 0, 
            aditivos_total=f.get("aditivos_total") or 0,
            data_inicio=data_inicio, 
            data_fim=data_fim,
            status=f.get("status","VIGENTE"),
            orcamento_id=(int(f["orcamento_id"]) if f.get("orcamento_id") else None)
        )
        c = criar_contrato(payload)
        flash("Contrato criado com sucesso.","success")
        return redirect(url_for("ui_contr.contr_list"))
    except Exception as e:
        flash(f"Erro ao criar contrato: {str(e)}", "danger")
        return render_template("contr_form.html", c=None)

@ui_contr.get("/contratos/<int:cid>/editar")
def contr_edit(cid):
    c = db.session.get(Contrato, cid)
    if not c:
        flash("Contrato não encontrado.", "danger")
        return redirect(url_for("ui_contr.contr_list"))
    return render_template("contr_form.html", c=c)

@ui_contr.post("/contratos/<int:cid>/editar")
def contr_update(cid):
    try:
        c = db.session.get(Contrato, cid)
        if not c:
            flash("Contrato não encontrado.", "danger")
            return redirect(url_for("ui_contr.contr_list"))
            
        f = request.form
        c.numero = f["numero"]
        c.fornecedor = f["fornecedor"]
        c.objeto = f.get("objeto")
        c.valor_inicial = float(f.get("valor_inicial") or 0)
        c.aditivos_total = float(f.get("aditivos_total") or 0)
        c.valor_atualizado = c.valor_inicial + c.aditivos_total
        
        # Conversão de datas
        if f.get("data_inicio"):
            c.data_inicio = datetime.strptime(f["data_inicio"], "%Y-%m-%d").date()
        else:
            c.data_inicio = None
            
        if f.get("data_fim"):
            c.data_fim = datetime.strptime(f["data_fim"], "%Y-%m-%d").date()
        else:
            c.data_fim = None
            
        c.status = f.get("status","VIGENTE")
        c.orcamento_id = int(f["orcamento_id"]) if f.get("orcamento_id") else None
        
        db.session.commit()
        flash("Contrato atualizado com sucesso.","success")
        return redirect(url_for("ui_contr.contr_list"))
    except Exception as e:
        flash(f"Erro ao atualizar contrato: {str(e)}", "danger")
        return redirect(url_for("ui_contr.contr_edit", cid=cid))

@ui_contr.get("/contratos/<int:cid>/aditivo")
def contr_aditivo(cid):
    c = db.session.get(Contrato, cid)
    if not c:
        flash("Contrato não encontrado.", "danger")
        return redirect(url_for("ui_contr.contr_list"))
    return render_template("contr_aditivo.html", c=c)

@ui_contr.post("/contratos/<int:cid>/aditivo")
def contr_aditivo_post(cid):
    try:
        v = float(request.form["valor"])
        aditivo_contrato(cid, v)
        flash("Aditivo aplicado com sucesso.","success")
    except Exception as e:
        flash(f"Erro ao aplicar aditivo: {str(e)}", "danger")
    return redirect(url_for("ui_contr.contr_list"))

@ui_contr.get("/contratos/<int:cid>/empenhar")
def contr_empenhar(cid):
    c = db.session.get(Contrato, cid)
    if not c:
        flash("Contrato não encontrado.", "danger")
        return redirect(url_for("ui_contr.contr_list"))
    return render_template("contr_empenhar.html", c=c)

@ui_contr.post("/contratos/<int:cid>/empenhar")
def contr_empenhar_post(cid):
    try:
        f = request.form
        payload = {
            "numero": f["numero"], 
            "fornecedor": f["fornecedor"],
            "valor": float(f["valor"]),
            "orcamento_id": int(f["orcamento_id"]) if f.get("orcamento_id") else None,
            "descricao": f.get("descricao", "")
        }
        empenhar_no_contrato(cid, payload)
        flash("Empenho criado e vinculado ao contrato com sucesso.","success")
    except Exception as e:
        flash(f"Erro ao criar empenho: {str(e)}", "danger")
    return redirect(url_for("ui_contr.contr_list"))
