from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from sqlalchemy import desc
from flask_login import login_required, current_user

# Importar modelos - ajuste conforme sua estrutura
try:
    from models import Contrato, AnotacaoContrato, db
except ImportError:
    # Caminho alternativo se estiver em estrutura diferente
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from models import Contrato, AnotacaoContrato, db

bp = Blueprint("contratos", __name__, url_prefix="/contratos")

def _to_date(v):
    """Converte valor para date"""
    if not v: 
        return None
    if isinstance(v, datetime): 
        return v.date()
    return v

def _to_float(v):
    """Converte valor para float"""
    try: 
        return float(v or 0)
    except Exception: 
        return 0.0

@bp.route("/", methods=["GET"], endpoint="index")
@login_required
def lista():
    """Lista todos os contratos com estatísticas"""
    # Buscar todos os contratos
    contratos = (Contrato.query.order_by(desc(Contrato.data_inicio)).all())

    # Calcular estatísticas
    hoje = date.today()
    em_30 = hoje + timedelta(days=30)

    total_contratos = len(contratos)
    total_ativos = 0
    vencendo_30 = 0
    valor_total_ativo = 0.0

    for c in contratos:
        st = (c.status or "").upper()
        if st == "ATIVO":
            total_ativos += 1
            valor_total_ativo += _to_float(c.valor_total)
        
        # Verificar contratos vencendo
        df = _to_date(c.data_fim)
        if df and hoje <= df <= em_30:
            vencendo_30 += 1

    return render_template(
        "contratos/index.html",  # ou "contratos/lista.html" se preferir
        contratos=contratos,
        total_contratos=total_contratos,
        total_ativos=total_ativos,
        vencendo_30=vencendo_30,
        valor_total_ativo=valor_total_ativo,
    )

@bp.route("/<int:contrato_id>/anotacoes", methods=["GET"])
@login_required
def anotacoes(contrato_id: int):
    """Buscar anotações de um contrato"""
    try:
        # Buscar anotações do contrato
        qs = (AnotacaoContrato.query
              .filter(AnotacaoContrato.contrato_id == contrato_id)
              .order_by(AnotacaoContrato.data_criacao.desc())
              .all())
        
        # Preparar payload
        payload = []
        for a in qs:
            # Buscar nome do usuário
            usuario_nome = "Sistema"
            if a.usuario:
                usuario_nome = getattr(a.usuario, "nome", getattr(a.usuario, "username", "Usuário"))
            
            anotacao_data = {
                "id": a.id,
                "texto": a.texto,
                "usuario": usuario_nome,
                "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None,
                "data_criacao_formatada": a.data_criacao.strftime("%d/%m/%Y %H:%M") if a.data_criacao else None,
            }
            
            # Adicionar informações do arquivo se existir
            if a.nome_arquivo:
                anotacao_data.update({
                    "nome_arquivo": a.nome_arquivo,
                    "tipo_arquivo": a.tipo_arquivo,
                    "tamanho_arquivo": a.tamanho_arquivo
                })
            
            payload.append(anotacao_data)
        
        return jsonify(success=True, anotacoes=payload)
    
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@bp.route("/<int:contrato_id>/anotacoes", methods=["POST"])
@login_required
def criar_anotacao(contrato_id: int):
    """Criar nova anotação para um contrato"""
    try:
        # Verificar se o contrato existe
        contrato = Contrato.query.get_or_404(contrato_id)
        
        # Obter dados do formulário
        texto = request.form.get('texto', '').strip()
        if not texto:
            return jsonify(success=False, error="Texto da anotação é obrigatório"), 400
        
        # Criar nova anotação
        anotacao = AnotacaoContrato(
            contrato_id=contrato_id,
            usuario_id=current_user.id,
            texto=texto
        )
        
        # Processar arquivo se enviado
        if 'arquivo' in request.files:
            arquivo = request.files['arquivo']
            if arquivo and arquivo.filename:
                # Aqui você pode implementar o upload do arquivo
                # Por enquanto, apenas salvar as informações
                anotacao.nome_arquivo = arquivo.filename
                anotacao.tipo_arquivo = arquivo.content_type
                # anotacao.tamanho_arquivo = len(arquivo.read())
                # arquivo.seek(0)  # Reset para salvar o arquivo
        
        # Salvar no banco
        db.session.add(anotacao)
        db.session.commit()
        
        return jsonify(success=True, message="Anotação criada com sucesso!")
    
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500

@bp.route("/<int:contrato_id>/anotacoes/<int:anotacao_id>", methods=["DELETE"])
@login_required
def excluir_anotacao(contrato_id: int, anotacao_id: int):
    """Excluir uma anotação"""
    try:
        # Buscar a anotação
        anotacao = AnotacaoContrato.query.filter_by(
            id=anotacao_id,
            contrato_id=contrato_id
        ).first_or_404()
        
        # Verificar se o usuário pode excluir (própria anotação ou admin)
        if anotacao.usuario_id != current_user.id and not current_user.is_admin:
            return jsonify(success=False, error="Sem permissão para excluir esta anotação"), 403
        
        # Excluir
        db.session.delete(anotacao)
        db.session.commit()
        
        return jsonify(success=True, message="Anotação excluída com sucesso!")
    
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500
