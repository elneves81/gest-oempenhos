from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime
from models import db, Contrato, Comunicacao

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

# --------- Helpers ---------
def etapa_status(contrato):
    """Calcula status de cada etapa com base nos campos do contrato."""
    return [
        {
            'id': 1,
            'nome': 'Criação do Contrato',
            'status': 'concluido',
            'data': contrato.data_criacao,
            'responsavel': 'Sistema',
            'descricao': 'Contrato criado no sistema'
        },
        {
            'id': 2,
            'nome': 'Assinatura',
            'status': 'concluido' if contrato.data_assinatura else 'pendente',
            'data': contrato.data_assinatura,
            'responsavel': 'Gestor',
            'descricao': 'Assinatura do contrato'
        },
        {
            'id': 3,
            'nome': 'Vigência',
            'status': 'em_andamento' if contrato.status and contrato.status.upper() == 'ATIVO' else ('concluido' if contrato.data_fim and contrato.data_fim < datetime.now().date() else 'pendente'),
            'data': contrato.data_inicio,
            'responsavel': 'Fiscal',
            'descricao': 'Período de vigência do contrato'
        },
        {
            'id': 4,
            'nome': 'Encerramento',
            'status': 'concluido' if contrato.status and contrato.status.upper() in ('ENCERRADO','FINALIZADO') else 'pendente',
            'data': contrato.data_fim,
            'responsavel': 'Gestor',
            'descricao': 'Encerramento do contrato'
        }
    ]

def badge_for_status(s):
    """Retorna classe CSS do badge para cada status"""
    return {
        'concluido': 'success',
        'em_andamento': 'warning',
        'pendente': 'secondary'
    }.get(s, 'secondary')


# --------- Dashboard com filtro e paginação ---------
@workflow_bp.route('/')
@login_required
def dashboard():
    """Dashboard principal do workflow com filtro e paginação."""
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 12, type=int), 50)

    query = Contrato.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Contrato.numero_contrato.ilike(like), 
            Contrato.objeto.ilike(like),
            Contrato.fornecedor.ilike(like)
        ))
    if status:
        query = query.filter(Contrato.status.ilike(status))

    contratos = query.order_by(Contrato.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Calcular estatísticas para os cards
    total_geral = contratos.total
    total_pagina = len(contratos.items)
    contratos_ativos = sum(1 for c in contratos.items if c.status and c.status.upper() == 'ATIVO')
    
    # Contratos vencendo em 30 dias
    vencendo_30_dias = 0
    for contrato in contratos.items:
        if hasattr(contrato, 'dias_para_vencimento') and contrato.dias_para_vencimento:
            if 0 <= contrato.dias_para_vencimento <= 30:
                vencendo_30_dias += 1

    return render_template('workflow/dashboard.html', 
                         contratos=contratos, 
                         q=q, 
                         status=status,
                         total_geral=total_geral,
                         total_pagina=total_pagina,
                         contratos_ativos=contratos_ativos,
                         vencendo_30_dias=vencendo_30_dias,
                         badge_for_status=badge_for_status)


# --------- Fluxo detalhado ---------
@workflow_bp.route('/fluxo/<int:contrato_id>')
@login_required
def fluxo_detalhado(contrato_id):
    """Visualizar fluxo detalhado de um contrato"""
    contrato = Contrato.query.get_or_404(contrato_id)
    etapas = etapa_status(contrato)
    return render_template('workflow/fluxo_detalhado.html', 
                         contrato=contrato, 
                         etapas=etapas, 
                         badge_for_status=badge_for_status)


# --------- Comunicações: listagem geral/por contrato ---------
@workflow_bp.route('/comunicacoes')
@workflow_bp.route('/comunicacoes/<int:contrato_id>')
@login_required
def comunicacoes(contrato_id=None):
    """Lista comunicações do workflow"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 15, type=int), 100)

    contrato = None
    if contrato_id:
        contrato = Contrato.query.get_or_404(contrato_id)
        query = contrato.comunicacoes.order_by(Comunicacao.criado_em.desc())
    else:
        query = Comunicacao.query.order_by(Comunicacao.criado_em.desc())

    comunicacoes = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('workflow/comunicacoes.html', 
                         contrato=contrato, 
                         comunicacoes=comunicacoes)


# --------- Criar comunicação (GET formulário + POST salvar) ---------
@workflow_bp.route('/comunicacao/nova/<int:contrato_id>', methods=['GET', 'POST'])
@login_required
def nova_comunicacao(contrato_id):
    """Criar nova comunicação"""
    contrato = Contrato.query.get_or_404(contrato_id)

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        remetente = request.form.get('remetente', '').strip() or getattr(current_user, 'nome', 'Sistema')

        if not titulo or not conteudo:
            flash('Preencha título e conteúdo.', 'warning')
            return render_template('workflow/nova_comunicacao.html', 
                                 contrato=contrato, 
                                 titulo=titulo, 
                                 conteudo=conteudo, 
                                 remetente=remetente), 400

        comm = Comunicacao(
            contrato_id=contrato.id, 
            titulo=titulo, 
            conteudo=conteudo, 
            remetente=remetente
        )
        db.session.add(comm)
        db.session.commit()
        flash('Comunicação criada com sucesso.', 'success')
        return redirect(url_for('workflow.comunicacoes', contrato_id=contrato.id))

    return render_template('workflow/nova_comunicacao.html', contrato=contrato)


# --------- Visualizar comunicação específica ---------
@workflow_bp.route('/comunicacao/<int:comunicacao_id>')
@login_required
def visualizar_comunicacao(comunicacao_id):
    """Visualizar comunicação específica"""
    comm = Comunicacao.query.get_or_404(comunicacao_id)
    return render_template('workflow/visualizar_comunicacao.html', 
                         comunicacao=comm, 
                         contrato=comm.contrato)


# --------- Deletar comunicação ---------
@workflow_bp.route('/comunicacao/<int:comunicacao_id>/excluir', methods=['POST'])
@login_required
def excluir_comunicacao(comunicacao_id):
    """Excluir comunicação"""
    comm = Comunicacao.query.get_or_404(comunicacao_id)
    contrato_id = comm.contrato_id
    db.session.delete(comm)
    db.session.commit()
    flash('Comunicação excluída.', 'info')
    return redirect(url_for('workflow.comunicacoes', contrato_id=contrato_id))


# --------- API JSON (útil pra AJAX) ---------
@workflow_bp.route('/api/contratos/<int:contrato_id>/fluxo')
@login_required
def api_fluxo(contrato_id):
    """API JSON para fluxo de contrato"""
    contrato = Contrato.query.get_or_404(contrato_id)
    etapas = etapa_status(contrato)
    return jsonify({
        'contrato_id': contrato.id,
        'status': contrato.status,
        'etapas': [
            {
                'id': e['id'],
                'nome': e['nome'],
                'status': e['status'],
                'data': e['data'].isoformat() if e['data'] else None,
                'responsavel': e['responsavel'],
                'descricao': e['descricao']
            } for e in etapas
        ]
    })


@workflow_bp.route('/api/contratos')
@login_required
def api_contratos():
    """API JSON para listar contratos"""
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    query = Contrato.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Contrato.numero_contrato.ilike(like), 
            Contrato.objeto.ilike(like)
        ))
    if status:
        query = query.filter(Contrato.status.ilike(status))
    
    data = [{
        'id': c.id,
        'numero': c.numero_contrato,
        'status': c.status,
        'data_criacao': c.data_criacao.isoformat() if c.data_criacao else None
    } for c in query.order_by(Contrato.data_criacao.desc()).limit(100).all()]
    
    return jsonify(data)
