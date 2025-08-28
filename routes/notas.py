from sqlalchemy.orm import joinedload
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract, and_, or_
import os

notas_bp = Blueprint('notas', __name__, url_prefix='/notas')

# Dependências que serão injetadas pelo app principal
NotaFiscal = None
Empenho = None
db = None

@notas_bp.route('/')
@login_required
def index():
    """Lista todas as notas fiscais"""
    # Filtros
    status = request.args.get('status', '')
    empenho_id = request.args.get('empenho_id', '', type=int)
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    fornecedor = request.args.get('fornecedor', '')
    
    # Query base
    query = NotaFiscal.query
    
    # Aplicar filtros
    if status:
        query = query.filter(NotaFiscal.status == status)
    
    if empenho_id:
        query = query.filter(NotaFiscal.empenho_id == empenho_id)
        
    if data_inicio:
        query = query.filter(NotaFiscal.data_emissao >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        
    if data_fim:
        query = query.filter(NotaFiscal.data_emissao <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        
    if fornecedor:
        query = query.filter(NotaFiscal.fornecedor_nome.ilike(f'%{fornecedor}%'))
    
    # Ordenação
    notas = query.order_by(NotaFiscal.data_emissao.desc()).all()
    
    # Estatísticas
    total_notas = NotaFiscal.query.options(joinedload(NotaFiscal.empenho).joinedload('contrato')).count()
    notas_em_aberto = NotaFiscal.query.filter_by(status='EM_ABERTO').count()
    notas_pagas = NotaFiscal.query.filter_by(status='PAGO').count()
    notas_vencidas = NotaFiscal.query.filter(
        and_(NotaFiscal.status == 'EM_ABERTO', 
             NotaFiscal.data_vencimento < date.today())
    ).count()
    
    # Valores
    valor_total_em_aberto = db.session.query(func.sum(NotaFiscal.valor_liquido)).filter_by(status='EM_ABERTO').scalar() or 0
    valor_total_pago = db.session.query(func.sum(NotaFiscal.valor_liquido)).filter_by(status='PAGO').scalar() or 0
    
    # Lista de empenhos para filtro
    empenhos = Empenho.query.order_by(Empenho.numero_empenho).all()
    
    return render_template('notas/index.html',
                         notas=notas,
                         empenhos=empenhos,
                         total_notas=total_notas,
                         notas_em_aberto=notas_em_aberto,
                         notas_pagas=notas_pagas,
                         notas_vencidas=notas_vencidas,
                         valor_total_em_aberto=valor_total_em_aberto,
                         valor_total_pago=valor_total_pago,
                         filtros={
                             'status': status,
                             'empenho_id': empenho_id,
                             'data_inicio': data_inicio,
                             'data_fim': data_fim,
                             'fornecedor': fornecedor
                         })

@notas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    """Criar nova nota fiscal"""
    if request.method == 'POST':
        try:
            # Criar nova nota fiscal
            nota = NotaFiscal.create_from_data({
                'numero_nota': request.form['numero_nota'],
                'serie': request.form.get('serie'),
                'chave_acesso': request.form.get('chave_acesso'),
                'empenho_id': int(request.form['empenho_id']),
                'fornecedor_nome': request.form['fornecedor_nome'],
                'fornecedor_cnpj': request.form['fornecedor_cnpj'],
                'data_emissao': datetime.strptime(request.form['data_emissao'], '%Y-%m-%d').date(),
                'data_vencimento': datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None,
                'data_recebimento': datetime.strptime(request.form['data_recebimento'], '%Y-%m-%d').date() if request.form.get('data_recebimento') else None,
                'valor_bruto': float(request.form['valor_bruto']),
                'valor_desconto': float(request.form.get('valor_desconto', 0)),
                'valor_ir': float(request.form.get('valor_ir', 0)),
                'valor_inss': float(request.form.get('valor_inss', 0)),
                'valor_iss': float(request.form.get('valor_iss', 0)),
                'valor_outros_impostos': float(request.form.get('valor_outros_impostos', 0)),
                'status': request.form.get('status', 'EM_ABERTO'),
                'observacoes': request.form.get('observacoes'),
                'usuario_id': current_user.id
            })
            
            db.session.add(nota)
            db.session.commit()
            flash('Nota fiscal criada com sucesso!', 'success')
            return redirect(url_for('notas.detalhes', id=nota.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao criar nota fiscal: {str(e)}', 'error')
            db.session.rollback()
    
    # Lista de empenhos para o formulário
    empenhos = Empenho.query.order_by(Empenho.numero_empenho).all()
    return render_template('notas/form.html', empenhos=empenhos)

@notas_bp.route('/<int:id>')
@login_required
def detalhes(id):
    """Visualizar detalhes da nota fiscal"""
    nota = NotaFiscal.query.get_or_404(id)
    return render_template('notas/detalhes.html', nota=nota)

@notas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar nota fiscal"""
    nota = NotaFiscal.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualizar campos
            nota.numero_nota = request.form['numero_nota']
            nota.serie = request.form.get('serie')
            nota.chave_acesso = request.form.get('chave_acesso')
            nota.empenho_id = int(request.form['empenho_id'])
            nota.fornecedor_nome = request.form['fornecedor_nome']
            nota.fornecedor_cnpj = request.form['fornecedor_cnpj']
            nota.data_emissao = datetime.strptime(request.form['data_emissao'], '%Y-%m-%d').date()
            nota.data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None
            nota.data_recebimento = datetime.strptime(request.form['data_recebimento'], '%Y-%m-%d').date() if request.form.get('data_recebimento') else None
            nota.valor_bruto = float(request.form['valor_bruto'])
            nota.valor_desconto = float(request.form.get('valor_desconto', 0))
            nota.valor_ir = float(request.form.get('valor_ir', 0))
            nota.valor_inss = float(request.form.get('valor_inss', 0))
            nota.valor_iss = float(request.form.get('valor_iss', 0))
            nota.valor_outros_impostos = float(request.form.get('valor_outros_impostos', 0))
            nota.status = request.form.get('status', 'EM_ABERTO')
            nota.observacoes = request.form.get('observacoes')
            
            # Recalcular valores
            nota.calcular_valores()
            
            db.session.commit()
            flash('Nota fiscal atualizada com sucesso!', 'success')
            return redirect(url_for('notas.detalhes', id=nota.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao atualizar nota fiscal: {str(e)}', 'error')
            db.session.rollback()
    
    # Lista de empenhos para o formulário
    empenhos = Empenho.query.order_by(Empenho.numero_empenho).all()
    return render_template('notas/form.html', nota=nota, empenhos=empenhos)

@notas_bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def pagar(id):
    """Marcar nota como paga"""
    nota = NotaFiscal.query.get_or_404(id)
    
    try:
        nota.status = 'PAGO'
        nota.data_pagamento = datetime.now().date()
        nota.forma_pagamento = request.form.get('forma_pagamento')
        nota.banco_pagamento = request.form.get('banco_pagamento')
        nota.agencia_pagamento = request.form.get('agencia_pagamento')
        nota.conta_pagamento = request.form.get('conta_pagamento')
        nota.documento_pagamento = request.form.get('documento_pagamento')
        
        db.session.commit()
        flash('Nota fiscal marcada como paga!', 'success')
        
    except Exception as e:
        flash(f'Erro ao processar pagamento: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('notas.detalhes', id=id))

@notas_bp.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    """Cancelar nota fiscal"""
    nota = NotaFiscal.query.get_or_404(id)
    
    try:
        nota.status = 'CANCELADO'
        db.session.commit()
        flash('Nota fiscal cancelada!', 'warning')
        
    except Exception as e:
        flash(f'Erro ao cancelar nota fiscal: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('notas.detalhes', id=id))

@notas_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Excluir nota fiscal"""
    nota = NotaFiscal.query.get_or_404(id)
    
    try:
        db.session.delete(nota)
        db.session.commit()
        flash('Nota fiscal excluída com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir nota fiscal: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('notas.index'))

@notas_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard das notas fiscais"""
    # Estatísticas por status
    stats_status = db.session.query(
        NotaFiscal.status,
        func.count(NotaFiscal.id).label('quantidade'),
        func.sum(NotaFiscal.valor_liquido).label('valor_total')
    ).group_by(NotaFiscal.status).all()
    
    # Notas vencendo nos próximos 30 dias
    data_limite = date.today() + timedelta(days=30)
    notas_vencendo = NotaFiscal.query.filter(
        and_(NotaFiscal.status == 'EM_ABERTO',
             NotaFiscal.data_vencimento.between(date.today(), data_limite))
    ).order_by(NotaFiscal.data_vencimento).all()
    
    # Notas por mês (últimos 12 meses)
    notas_por_mes = db.session.query(
        extract('year', NotaFiscal.data_emissao).label('ano'),
        extract('month', NotaFiscal.data_emissao).label('mes'),
        func.count(NotaFiscal.id).label('quantidade'),
        func.sum(NotaFiscal.valor_liquido).label('valor_total')
    ).group_by('ano', 'mes').order_by('ano', 'mes').limit(12).all()
    
    # Top fornecedores
    top_fornecedores = db.session.query(
        NotaFiscal.fornecedor_nome,
        func.count(NotaFiscal.id).label('quantidade'),
        func.sum(NotaFiscal.valor_liquido).label('valor_total')
    ).group_by(NotaFiscal.fornecedor_nome).order_by(func.sum(NotaFiscal.valor_liquido).desc()).limit(10).all()
    
    return render_template('notas/dashboard.html',
                         stats_status=stats_status,
                         notas_vencendo=notas_vencendo,
                         notas_por_mes=notas_por_mes,
                         top_fornecedores=top_fornecedores)

@notas_bp.route('/api/empenho/<int:empenho_id>')
@login_required
def api_empenho_dados(empenho_id):
    """API para obter dados do empenho para preenchimento automático"""
    empenho = Empenho.query.get_or_404(empenho_id)
    
    return jsonify({
        'fornecedor_nome': empenho.fornecedores or '',
        'numero_contrato': empenho.numero_contrato or '',
        'valor_empenhado': float(empenho.valor_empenhado or 0),
        'cpf_cnpj_credor': empenho.cpf_cnpj_credor or ''
    })
