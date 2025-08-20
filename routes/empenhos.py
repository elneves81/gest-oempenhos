from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Empenho, Contrato, AditivoContratual, db
from datetime import datetime
import json

empenhos_bp = Blueprint('empenhos', __name__)

@empenhos_bp.route('/')
@login_required
def index():
    """Lista todos os empenhos com estatísticas"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtros
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Empenho.query
    
    if search:
        query = query.filter(
            db.or_(
                Empenho.numero_empenho.contains(search),
                Empenho.numero_pregao.contains(search),
                Empenho.numero_contrato.contains(search),
                Empenho.objeto.contains(search)
            )
        )
    
    if status:
        query = query.filter(Empenho.status == status)
    
    empenhos = query.order_by(Empenho.data_criacao.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Estatísticas para os cards
    total_empenhos = Empenho.query.count()
    valor_total_empenhos = db.session.query(db.func.sum(Empenho.valor_empenhado)).scalar() or 0
    empenhos_recentes = Empenho.query.order_by(Empenho.data_criacao.desc()).limit(10).all()
    
    # Status dos empenhos
    empenhos_pendentes = Empenho.query.filter_by(status='PENDENTE').count()
    empenhos_aprovados = Empenho.query.filter_by(status='APROVADO').count()
    empenhos_pagos = Empenho.query.filter_by(status='PAGO').count()
    empenhos_rejeitados = Empenho.query.filter_by(status='REJEITADO').count()
    
    return render_template('empenhos/index.html', 
                         empenhos=empenhos, 
                         search=search, 
                         status=status,
                         # Estatísticas
                         total_empenhos=total_empenhos,
                         valor_total_empenhos=valor_total_empenhos,
                         empenhos_recentes=empenhos_recentes,
                         empenhos_pendentes=empenhos_pendentes,
                         empenhos_aprovados=empenhos_aprovados,
                         empenhos_pagos=empenhos_pagos,
                         empenhos_rejeitados=empenhos_rejeitados)

@empenhos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Criar novo empenho"""
    if request.method == 'POST':
        try:
            empenho = Empenho(
                # Identificadores básicos
                numero_pregao=request.form['numero_pregao'],
                numero_ctr=request.form.get('numero_ctr'),
                resumo_objeto=request.form['resumo_objeto'],
                fornecedores=request.form.get('fornecedores'),
                numero_contrato=request.form['numero_contrato'],
                numero_empenho=request.form['numero_empenho'],
                
                # Compatibilidade
                objeto=request.form.get('resumo_objeto', ''),  # Use resumo_objeto como objeto
                numero_aditivo=request.form.get('numero_aditivo'),
                
                # Gestão fiscal
                gestor_fiscal_e_superior=request.form.get('gestor_fiscal_e_superior'),
                
                # Datas principais
                data_assinatura=datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date() if request.form.get('data_assinatura') else None,
                data_limite=datetime.strptime(request.form['data_limite'], '%Y-%m-%d').date() if request.form.get('data_limite') else None,
                data_empenho=datetime.strptime(request.form['data_empenho'], '%Y-%m-%d').date(),
                data_vencimento=datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None,
                
                # Informações Orçamentárias e Fiscais
                dotacao_orcamentaria=request.form.get('dotacao_orcamentaria'),
                fonte_recursos=request.form.get('fonte_recursos'),
                modalidade_aplicacao=request.form.get('modalidade_aplicacao'),
                elemento_despesa=request.form.get('elemento_despesa'),
                processo_administrativo=request.form.get('processo_administrativo'),
                cpf_cnpj_credor=request.form.get('cpf_cnpj_credor'),
                
                # Valores financeiros
                valor_empenhado=float(request.form['valor_empenhado']),
                valor_periodo=float(request.form['valor_periodo']) if request.form.get('valor_periodo') else None,
                percentual_retencao=float(request.form.get('percentual_retencao', 0)),
                
                # Outros campos
                status=request.form.get('status', 'PENDENTE'),
                nota_fiscal=request.form.get('nota_fiscal'),
                periodo_referencia=request.form.get('periodo_referencia'),
                observacoes=request.form.get('observacoes'),
                
                # Campos antigos mantidos para compatibilidade
                unidade_mensal=request.form.get('unidade_mensal'),
                valor_unitario=float(request.form['valor_unitario']) if request.form.get('valor_unitario') else None,
                quantidade=float(request.form['quantidade']) if request.form.get('quantidade') else None,
                data_envio=datetime.strptime(request.form['data_envio'], '%Y-%m-%d').date() if request.form.get('data_envio') else None,
                
                # Metadados
                usuario_id=current_user.id
            )
            
            # Calcular valores automaticamente
            empenho.calcular_valores()
            
            db.session.add(empenho)
            db.session.commit()
            
            flash('Empenho criado com sucesso!', 'success')
            return redirect(url_for('empenhos.detalhes', id=empenho.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao criar empenho: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('empenhos/form_completo.html', empenho=None)

@empenhos_bp.route('/novo-completo', methods=['GET', 'POST'])
@login_required
def novo_completo():
    """Criar novo empenho com formulário completo - alias para novo()"""
    return novo()

@empenhos_bp.route('/<int:id>')
@login_required
def detalhes(id):
    """Detalhes de um empenho"""
    empenho = Empenho.query.get_or_404(id)
    return render_template('empenhos/detalhes.html', empenho=empenho)

@empenhos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar empenho"""
    empenho = Empenho.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Campos de identificação
            empenho.numero_pregao = request.form['numero_pregao']
            empenho.numero_contrato = request.form['numero_contrato']
            empenho.numero_aditivo = request.form.get('numero_aditivo')
            empenho.numero_ctr = request.form.get('numero_ctr')
            
            # Objeto e fornecedores
            empenho.resumo_objeto = request.form.get('resumo_objeto', '')
            empenho.objeto = request.form.get('resumo_objeto', '')  # Compatibilidade
            empenho.fornecedores = request.form.get('fornecedores')
            empenho.gestor_fiscal_e_superior = request.form.get('gestor_fiscal_e_superior')
            
            # Valores e unidades
            empenho.unidade_mensal = request.form.get('unidade_mensal')
            empenho.valor_unitario = None  # Campo não existe no formulário
            empenho.numero_empenho = request.form['numero_empenho']
            empenho.valor_empenhado = float(request.form['valor_empenhado'])
            empenho.quantidade = None  # Campo não existe no formulário
            empenho.valor_periodo = float(request.form['valor_periodo']) if request.form.get('valor_periodo') else None
            empenho.percentual_retencao = float(request.form.get('percentual_retencao', 0))
            
            # Datas principais
            empenho.data_empenho = datetime.strptime(request.form['data_empenho'], '%Y-%m-%d').date()
            empenho.data_assinatura = datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date() if request.form.get('data_assinatura') else None
            empenho.data_limite = datetime.strptime(request.form['data_limite'], '%Y-%m-%d').date() if request.form.get('data_limite') else None
            empenho.data_envio = None  # Campo não existe no formulário
            empenho.data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None
            
            # Informações Orçamentárias e Fiscais
            empenho.dotacao_orcamentaria = request.form.get('dotacao_orcamentaria')
            empenho.fonte_recursos = request.form.get('fonte_recursos')
            empenho.modalidade_aplicacao = request.form.get('modalidade_aplicacao')
            empenho.elemento_despesa = request.form.get('elemento_despesa')
            empenho.processo_administrativo = request.form.get('processo_administrativo')
            empenho.cpf_cnpj_credor = request.form.get('cpf_cnpj_credor')
            
            # Outros campos
            empenho.periodo_referencia = request.form.get('periodo_referencia')
            empenho.status = request.form.get('status', 'PENDENTE')
            empenho.nota_fiscal = request.form.get('nota_fiscal')
            empenho.observacoes = request.form.get('observacoes')
            
            # Recalcular valores
            empenho.calcular_valores()
            
            db.session.commit()
            flash('Empenho atualizado com sucesso!', 'success')
            return redirect(url_for('empenhos.detalhes', id=empenho.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao atualizar empenho: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('empenhos/form_completo.html', empenho=empenho)

@empenhos_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Excluir empenho"""
    empenho = Empenho.query.get_or_404(id)
    
    try:
        db.session.delete(empenho)
        db.session.commit()
        flash('Empenho excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir empenho: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('empenhos.index'))

@empenhos_bp.route('/api/calcular-valores', methods=['POST'])
@login_required
def calcular_valores():
    """API para calcular valores automaticamente"""
    data = request.get_json()
    
    valor_empenhado = float(data.get('valor_empenhado', 0))
    percentual_retencao = float(data.get('percentual_retencao', 0))
    
    valor_retencao = valor_empenhado * (percentual_retencao / 100)
    valor_liquido = valor_empenhado - valor_retencao
    
    return jsonify({
        'valor_retencao': round(valor_retencao, 2),
        'valor_liquido': round(valor_liquido, 2)
    })

@empenhos_bp.route('/contratos')
@login_required
def contratos():
    """Lista de contratos"""
    contratos = Contrato.query.all()
    return render_template('empenhos/contratos.html', contratos=contratos)

@empenhos_bp.route('/contratos/novo', methods=['GET', 'POST'])
@login_required
def novo_contrato():
    """Criar novo contrato"""
    if request.method == 'POST':
        try:
            contrato = Contrato(
                numero_pregao=request.form['numero_pregao'],
                numero_contrato=request.form['numero_contrato'],
                objeto=request.form['objeto'],
                fornecedor=request.form['fornecedor'],
                valor_total=float(request.form['valor_total']),
                data_assinatura=datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date(),
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                data_fim=datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date(),
                status=request.form.get('status', 'ATIVO')
            )
            
            db.session.add(contrato)
            db.session.commit()
            
            flash('Contrato criado com sucesso!', 'success')
            return redirect(url_for('empenhos.contratos'))
            
        except Exception as e:
            flash(f'Erro ao criar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/form_novo.html', contrato=None)

@empenhos_bp.route('/contratos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_contrato(id):
    """Editar contrato existente"""
    contrato = Contrato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            contrato.numero_pregao = request.form['numero_pregao']
            contrato.numero_contrato = request.form['numero_contrato']
            contrato.objeto = request.form['objeto']
            contrato.fornecedor = request.form['fornecedor']
            contrato.valor_total = float(request.form['valor_total'])
            contrato.data_assinatura = datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date()
            contrato.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
            contrato.data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date()
            contrato.status = request.form.get('status', 'ATIVO')
            
            db.session.commit()
            
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('empenhos.contratos'))
            
        except Exception as e:
            flash(f'Erro ao atualizar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('empenhos/contrato_form.html', contrato=contrato)

@empenhos_bp.route('/contratos/<int:id>')
@login_required
def visualizar_contrato(id):
    """Visualizar detalhes do contrato"""
    contrato = Contrato.query.get_or_404(id)
    empenhos = Empenho.query.filter_by(contrato_id=id).all()
    return render_template('empenhos/contrato_detalhes.html', contrato=contrato, empenhos=empenhos)

@empenhos_bp.route('/contratos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_contrato(id):
    """Excluir contrato"""
    contrato = Contrato.query.get_or_404(id)
    force = request.form.get('force', 'false').lower() == 'true'
    
    try:
        # Verificar se há empenhos vinculados
        empenhos_vinculados = Empenho.query.filter_by(contrato_id=id).count()
        if empenhos_vinculados > 0:
            flash(f'Não é possível excluir o contrato. Há {empenhos_vinculados} empenho(s) vinculado(s).', 'error')
            return redirect(url_for('empenhos.contratos'))
        
        # Verificar se há aditivos vinculados
        aditivos_vinculados = AditivoContratual.query.filter_by(contrato_id=id).count()
        if aditivos_vinculados > 0 and not force:
            flash(f'O contrato possui {aditivos_vinculados} aditivo(s) que serão excluídos automaticamente junto com o contrato. Confirme a exclusão para prosseguir.', 'warning')
            return redirect(url_for('empenhos.contratos'))
        
        # Se chegou aqui, pode excluir (cascade irá excluir os aditivos automaticamente)
        db.session.delete(contrato)
        db.session.commit()
        
        if aditivos_vinculados > 0:
            flash(f'Contrato e {aditivos_vinculados} aditivo(s) excluídos com sucesso!', 'success')
        else:
            flash('Contrato excluído com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro ao excluir contrato: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('empenhos.contratos'))

@empenhos_bp.route('/status/<status>')
@login_required
def por_status(status):
    """Filtrar empenhos por status"""
    empenhos = Empenho.query.filter_by(status=status).order_by(Empenho.data_criacao.desc()).all()
    return render_template('empenhos/por_status.html', empenhos=empenhos, status=status)
