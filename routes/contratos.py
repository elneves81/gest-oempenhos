from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Contrato, AditivoContratual

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

@contratos_bp.route('/')
@login_required
def index():
    """Lista todos os contratos"""
    # Filtros de busca
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Contrato.query
    
    if search:
        query = query.filter(
            db.or_(
                Contrato.numero_contrato.ilike(f'%{search}%'),
                Contrato.numero_pregao.ilike(f'%{search}%'),
                Contrato.objeto.ilike(f'%{search}%'),
                Contrato.fornecedor.ilike(f'%{search}%')
            )
        )
    
    if status:
        query = query.filter(Contrato.status == status)
    
    contratos = query.order_by(Contrato.data_criacao.desc()).all()
    
    return render_template('contratos/index.html', 
                         contratos=contratos, 
                         search=search, 
                         status=status)

@contratos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Criar novo contrato"""
    if request.method == 'POST':
        try:
            contrato = Contrato(
                # Identificação
                numero_pregao=request.form['numero_pregao'],
                numero_contrato=request.form['numero_contrato'],
                numero_ctr=request.form.get('numero_ctr'),
                
                # Objeto e fornecedor
                objeto=request.form['objeto'],
                resumo_objeto=request.form.get('resumo_objeto'),
                fornecedor=request.form['fornecedor'],
                
                # Valores
                valor_total=float(request.form['valor_total']),
                valor_inicial=float(request.form['valor_total']),  # Inicialmente igual
                
                # Datas
                data_assinatura=datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date(),
                data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date(),
                data_fim=datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date(),
                data_fim_original=datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date(),
                
                # Gestão
                gestor_fiscal=request.form.get('gestor_fiscal'),
                gestor_superior=request.form.get('gestor_superior'),
                status=request.form.get('status', 'ATIVO'),
                
                # Informações municipais
                modalidade_licitacao=request.form.get('modalidade_licitacao'),
                numero_processo=request.form.get('numero_processo'),
                lei_base=request.form.get('lei_base'),
                orgao_contratante=request.form.get('orgao_contratante'),
                secretaria=request.form.get('secretaria'),
                
                # Garantias
                tipo_garantia=request.form.get('tipo_garantia'),
                valor_garantia=float(request.form['valor_garantia']) if request.form.get('valor_garantia') else None,
                validade_garantia=datetime.strptime(request.form['validade_garantia'], '%Y-%m-%d').date() if request.form.get('validade_garantia') else None,
                
                # Observações
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(contrato)
            db.session.commit()
            
            flash('Contrato criado com sucesso!', 'success')
            return redirect(url_for('contratos.detalhes', id=contrato.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao criar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/form.html', contrato=None)

@contratos_bp.route('/<int:id>')
@login_required
def detalhes(id):
    """Detalhes de um contrato"""
    contrato = Contrato.query.get_or_404(id)
    return render_template('contratos/detalhes.html', contrato=contrato)

@contratos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualizar campos
            contrato.numero_pregao = request.form['numero_pregao']
            contrato.numero_contrato = request.form['numero_contrato']
            contrato.numero_ctr = request.form.get('numero_ctr')
            contrato.objeto = request.form['objeto']
            contrato.resumo_objeto = request.form.get('resumo_objeto')
            contrato.fornecedor = request.form['fornecedor']
            contrato.valor_total = float(request.form['valor_total'])
            contrato.data_assinatura = datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date()
            contrato.data_inicio = datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
            contrato.data_fim = datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date()
            contrato.gestor_fiscal = request.form.get('gestor_fiscal')
            contrato.gestor_superior = request.form.get('gestor_superior')
            contrato.status = request.form.get('status', 'ATIVO')
            contrato.modalidade_licitacao = request.form.get('modalidade_licitacao')
            contrato.numero_processo = request.form.get('numero_processo')
            contrato.lei_base = request.form.get('lei_base')
            contrato.orgao_contratante = request.form.get('orgao_contratante')
            contrato.secretaria = request.form.get('secretaria')
            contrato.tipo_garantia = request.form.get('tipo_garantia')
            contrato.valor_garantia = float(request.form['valor_garantia']) if request.form.get('valor_garantia') else None
            contrato.validade_garantia = datetime.strptime(request.form['validade_garantia'], '%Y-%m-%d').date() if request.form.get('validade_garantia') else None
            contrato.observacoes = request.form.get('observacoes')
            
            db.session.commit()
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('contratos.detalhes', id=contrato.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao atualizar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/form.html', contrato=contrato)

@contratos_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    """Excluir contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    try:
        db.session.delete(contrato)
        db.session.commit()
        flash('Contrato excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir contrato: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('contratos.index'))

# Rotas para Aditivos Contratuais
@contratos_bp.route('/<int:contrato_id>/aditivos/novo', methods=['GET', 'POST'])
@login_required
def novo_aditivo(contrato_id):
    """Criar novo aditivo contratual"""
    contrato = Contrato.query.get_or_404(contrato_id)
    
    if request.method == 'POST':
        try:
            # Determinar próximo número de aditivo
            ultimo_aditivo = AditivoContratual.query.filter_by(contrato_id=contrato_id).order_by(AditivoContratual.numero_aditivo.desc()).first()
            proximo_numero = (ultimo_aditivo.numero_aditivo + 1) if ultimo_aditivo else 1
            
            aditivo = AditivoContratual(
                contrato_id=contrato_id,
                numero_aditivo=proximo_numero,
                numero_instrumento=request.form.get('numero_instrumento'),
                tipo=request.form['tipo'],
                finalidade=request.form.get('finalidade'),
                valor_financeiro=float(request.form['valor_financeiro']) if request.form.get('valor_financeiro') else None,
                percentual=float(request.form['percentual']) if request.form.get('percentual') else None,
                prazo_prorrogacao=int(request.form['prazo_prorrogacao']) if request.form.get('prazo_prorrogacao') else None,
                nova_data_fim=datetime.strptime(request.form['nova_data_fim'], '%Y-%m-%d').date() if request.form.get('nova_data_fim') else None,
                data_assinatura=datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date(),
                data_publicacao=datetime.strptime(request.form['data_publicacao'], '%Y-%m-%d').date() if request.form.get('data_publicacao') else None,
                data_inicio_vigencia=datetime.strptime(request.form['data_inicio_vigencia'], '%Y-%m-%d').date() if request.form.get('data_inicio_vigencia') else None,
                fundamentacao_legal=request.form.get('fundamentacao_legal'),
                justificativa=request.form.get('justificativa'),
                observacoes=request.form.get('observacoes'),
                usuario_id=current_user.id
            )
            
            # Atualizar contrato se for prorrogação
            if aditivo.tipo == 'PRORROGACAO' and aditivo.nova_data_fim:
                contrato.data_fim = aditivo.nova_data_fim
            
            # Atualizar valor do contrato se for reajuste ou acréscimo
            if aditivo.tipo in ['REAJUSTE', 'ACRESCIMO'] and aditivo.valor_financeiro:
                contrato.valor_total = float(contrato.valor_total) + float(aditivo.valor_financeiro)
            
            db.session.add(aditivo)
            db.session.commit()
            
            flash(f'{aditivo.numero_aditivo}º Aditivo criado com sucesso!', 'success')
            return redirect(url_for('contratos.index'))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao criar aditivo: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/aditivo_form.html', contrato=contrato, aditivo=None)

@contratos_bp.route('/<int:contrato_id>/aditivos/<int:aditivo_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_aditivo(contrato_id, aditivo_id):
    """Editar aditivo contratual"""
    contrato = Contrato.query.get_or_404(contrato_id)
    aditivo = AditivoContratual.query.get_or_404(aditivo_id)
    
    if request.method == 'POST':
        try:
            aditivo.numero_instrumento = request.form.get('numero_instrumento')
            aditivo.tipo = request.form['tipo']
            aditivo.finalidade = request.form.get('finalidade')
            aditivo.valor_financeiro = float(request.form['valor_financeiro']) if request.form.get('valor_financeiro') else None
            aditivo.percentual = float(request.form['percentual']) if request.form.get('percentual') else None
            aditivo.prazo_prorrogacao = int(request.form['prazo_prorrogacao']) if request.form.get('prazo_prorrogacao') else None
            aditivo.nova_data_fim = datetime.strptime(request.form['nova_data_fim'], '%Y-%m-%d').date() if request.form.get('nova_data_fim') else None
            aditivo.data_assinatura = datetime.strptime(request.form['data_assinatura'], '%Y-%m-%d').date()
            aditivo.data_publicacao = datetime.strptime(request.form['data_publicacao'], '%Y-%m-%d').date() if request.form.get('data_publicacao') else None
            aditivo.data_inicio_vigencia = datetime.strptime(request.form['data_inicio_vigencia'], '%Y-%m-%d').date() if request.form.get('data_inicio_vigencia') else None
            aditivo.fundamentacao_legal = request.form.get('fundamentacao_legal')
            aditivo.justificativa = request.form.get('justificativa')
            aditivo.observacoes = request.form.get('observacoes')
            
            db.session.commit()
            flash('Aditivo atualizado com sucesso!', 'success')
            return redirect(url_for('contratos.index'))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao atualizar aditivo: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/aditivo_form.html', contrato=contrato, aditivo=aditivo)

@contratos_bp.route('/<int:contrato_id>/aditivos/<int:aditivo_id>/excluir', methods=['POST'])
@login_required
def excluir_aditivo(contrato_id, aditivo_id):
    """Excluir aditivo contratual"""
    aditivo = AditivoContratual.query.get_or_404(aditivo_id)
    
    try:
        db.session.delete(aditivo)
        db.session.commit()
        flash('Aditivo excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir aditivo: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('contratos.index'))

# Rotas AJAX para Modal de Aditivos
@contratos_bp.route('/<int:contrato_id>/aditivos')
def listar_aditivos_ajax(contrato_id):
    """Listar aditivos via AJAX para o modal"""
    # Verificar se o usuário está logado
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    contrato = Contrato.query.get_or_404(contrato_id)
    
    aditivos_data = []
    for aditivo in contrato.aditivos:
        aditivos_data.append({
            'id': aditivo.id,
            'numero_aditivo': aditivo.numero_aditivo,
            'tipo': aditivo.tipo,
            'data_aditivo': aditivo.data_assinatura.isoformat() if aditivo.data_assinatura else None,
            'valor_financeiro': float(aditivo.valor_financeiro) if aditivo.valor_financeiro else None,
            'prazo_dias': aditivo.prazo_prorrogacao,
            'justificativa': aditivo.justificativa
        })
    
    return jsonify({
        'success': True,
        'aditivos': aditivos_data
    })

@contratos_bp.route('/test-auth')
def test_auth():
    """Testar autenticação"""
    return jsonify({
        'is_authenticated': current_user.is_authenticated,
        'user_id': current_user.get_id() if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None
    })

@contratos_bp.route('/aditivos/criar', methods=['POST'])
def criar_aditivo_ajax():
    """Criar aditivo via AJAX"""
    # Verificar se o usuário está logado
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        contrato_id = request.form.get('contrato_id')
        contrato = Contrato.query.get_or_404(contrato_id)
        
        # Verificar se o número do aditivo já existe
        numero_aditivo = int(request.form['numero_aditivo'])
        aditivo_existente = AditivoContratual.query.filter_by(
            contrato_id=contrato_id, 
            numero_aditivo=numero_aditivo
        ).first()
        
        if aditivo_existente:
            return jsonify({
                'success': False,
                'error': f'{numero_aditivo}° Termo Aditivo já existe para este contrato.'
            })
        
        # Criar novo aditivo
        aditivo = AditivoContratual(
            contrato_id=contrato_id,
            numero_aditivo=numero_aditivo,
            tipo=request.form['tipo'],
            data_assinatura=datetime.strptime(request.form['data_aditivo'], '%Y-%m-%d').date(),
            justificativa=request.form['justificativa']
        )
        
        # Campos opcionais
        if request.form.get('valor_financeiro'):
            aditivo.valor_financeiro = float(request.form['valor_financeiro'])
        
        if request.form.get('prazo_dias'):
            aditivo.prazo_prorrogacao = int(request.form['prazo_dias'])
        
        if request.form.get('nova_data_fim'):
            aditivo.nova_data_fim = datetime.strptime(request.form['nova_data_fim'], '%Y-%m-%d').date()
            # Atualizar data_fim do contrato se fornecida
            contrato.data_fim = aditivo.nova_data_fim
        
        db.session.add(aditivo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aditivo criado com sucesso!'
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Erro nos dados fornecidos: {str(e)}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao criar aditivo: {str(e)}'
        })

@contratos_bp.route('/aditivos/<int:aditivo_id>/excluir', methods=['DELETE'])
def excluir_aditivo_ajax(aditivo_id):
    """Excluir aditivo via AJAX"""
    # Verificar se o usuário está logado
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    
    try:
        aditivo = AditivoContratual.query.get_or_404(aditivo_id)
        
        db.session.delete(aditivo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Aditivo excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir aditivo: {str(e)}'
        })
