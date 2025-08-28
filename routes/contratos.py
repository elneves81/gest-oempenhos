from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_file, abort
from flask_login import login_required, current_user
from datetime import datetime
import os
from models import db, Contrato, AditivoContratual, Empenho, ItemContrato, AnotacaoContrato, AnexoAnotacao

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

def parse_date_field(date_str):
    """
    Converte string de data de forma robusta.
    Aceita formatos: YYYY-MM-DD, YYYY, ou string vazia
    """
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # Se for apenas ano (4 dígitos)
    if len(date_str) == 4 and date_str.isdigit():
        return datetime(int(date_str), 1, 1).date()
    
    # Se for data completa
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # Tentar outros formatos comuns
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y').date()
            except ValueError:
                return None

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
    
    contratos = query.order_by(Contrato.id.desc()).all()

    return render_template('contratos/index.html', 
                         contratos=contratos, 
                         search=search, 
                         status=status)

@contratos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Criar novo contrato com WTForms"""
    from forms.contrato import ContratoForm
    
    form = ContratoForm()
    
    if form.validate_on_submit():
        try:
            # Upload de arquivo com validação automática
            arquivo_contrato = None
            if form.arquivo_contrato.data:
                arquivo_contrato = _upload_arquivo(form.arquivo_contrato.data)
            
            # Criar contrato usando dados validados do form
            contrato = Contrato(
                # Identificação
                numero_pregao=form.numero_pregao.data,
                data_pregao=form.data_pregao.data,
                numero_contrato=form.numero_contrato.data,
                data_contrato=form.data_contrato.data,
                numero_processo=form.numero_processo.data,
                data_processo=form.data_processo.data,
                digito_verificador=form.digito_verificador.data,
                tipo_contratacao=form.tipo_contratacao.data,
                
                # Objeto e fundamentação
                objeto=form.objeto.data,
                lei_base=form.lei_base.data,
                fornecedor=form.fornecedor.data,
                
                # Dados do fornecedor (CNPJ já validado)
                cnpj_fornecedor=form.cnpj_fornecedor.data,
                responsavel_nome=form.responsavel_nome.data,
                responsavel_email=form.responsavel_email.data,
                responsavel_telefone=form.responsavel_telefone.data,
                responsavel_cargo=form.responsavel_cargo.data,
                
                # Valores (decimais já convertidos)
                valor_total=form.valor_total.data,
                valor_inicial=form.valor_inicial.data or form.valor_total.data,
                
                # Datas
                data_assinatura=form.data_assinatura.data or datetime.now().date(),
                data_inicio=form.data_inicio.data or datetime.now().date(),
                data_fim=form.data_fim.data or datetime.now().date(),
                
                # Gestão
                gestor=form.gestor.data,
                gestor_suplente=form.gestor_suplente.data,
                fiscal=form.fiscal.data,
                fiscal_suplente=form.fiscal_suplente.data,
                status=form.status.data,
                
                # Informações municipais
                modalidade_licitacao=form.modalidade_licitacao.data,
                orgao_contratante=form.orgao_contratante.data,
                secretaria=form.secretaria.data,
                
                # Garantias
                tipo_garantia=form.tipo_garantia.data,
                valor_garantia=form.valor_garantia.data,
                validade_garantia=form.validade_garantia.data,
                
                # Arquivo e observações
                arquivo_contrato=arquivo_contrato,
                observacoes=form.observacoes.data
            )
            
            db.session.add(contrato)
            db.session.flush()  # Para obter o ID do contrato
            
            # Processar itens do contrato (se houver)
            # processar_itens_contrato(contrato, request.form)
            
            db.session.commit()
            
            flash('Contrato criado com sucesso! ✅ CNPJ validado, valores convertidos corretamente.', 'success')
            return redirect(url_for('contratos.detalhes', id=contrato.id))
            
        except Exception as e:
            flash(f'Erro ao criar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    # Se GET ou formulário inválido, mostrar erros de validação
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return render_template('contratos/form_wtf.html', form=form)


def _upload_arquivo(file_data):
    """Helper para upload de arquivos"""
    import os
    from werkzeug.utils import secure_filename
    
    # Criar diretório se não existir
    upload_path = os.path.join(current_app.root_path, 'uploads', 'contratos')
    os.makedirs(upload_path, exist_ok=True)
    
    # Salvar arquivo
    filename = secure_filename(file_data.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = timestamp + filename
    file_data.save(os.path.join(upload_path, filename))
    
    return filename

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
            # Atualizar campos básicos
            contrato.numero_pregao = request.form['numero_pregao']
            contrato.data_pregao = parse_date_field(request.form.get('data_pregao'))
            contrato.numero_contrato = request.form['numero_contrato']
            contrato.data_contrato = parse_date_field(request.form.get('data_contrato'))
            contrato.numero_processo = request.form.get('numero_processo')
            contrato.data_processo = parse_date_field(request.form.get('data_processo'))
            contrato.digito_verificador = request.form.get('digito_verificador')
            contrato.tipo_contratacao = request.form.get('tipo_contratacao')
            
            # Objeto e fundamentação
            contrato.objeto = request.form['objeto']
            contrato.lei_base = request.form.get('lei_base')
            contrato.fornecedor = request.form['fornecedor']
            
            # Dados do fornecedor
            contrato.cnpj_fornecedor = request.form.get('cnpj_fornecedor')
            contrato.responsavel_nome = request.form.get('responsavel_nome')
            contrato.responsavel_email = request.form.get('responsavel_email')
            contrato.responsavel_telefone = request.form.get('responsavel_telefone')
            contrato.responsavel_cargo = request.form.get('responsavel_cargo')
            
            # Valores
            contrato.valor_total = float(request.form['valor_total'])
            contrato.valor_inicial = float(request.form['valor_inicial']) if request.form.get('valor_inicial') else contrato.valor_inicial
            
            # Datas
            contrato.data_assinatura = parse_date_field(request.form.get('data_assinatura')) or contrato.data_assinatura
            contrato.data_inicio = parse_date_field(request.form.get('data_inicio')) or contrato.data_inicio
            contrato.data_fim = parse_date_field(request.form.get('data_fim')) or contrato.data_fim
            if request.form.get('data_fim_original'):
                contrato.data_fim_original = parse_date_field(request.form.get('data_fim_original'))
            
            # Gestão - campos atualizados
            contrato.gestor = request.form.get('gestor')
            contrato.gestor_suplente = request.form.get('gestor_suplente')
            contrato.fiscal = request.form.get('fiscal')
            contrato.fiscal_suplente = request.form.get('fiscal_suplente')
            contrato.status = request.form.get('status', 'ATIVO')
            
            # Informações municipais
            contrato.modalidade_licitacao = request.form.get('modalidade_licitacao')
            contrato.orgao_contratante = request.form.get('orgao_contratante')
            contrato.secretaria = request.form.get('secretaria')
            
            # Garantias
            contrato.tipo_garantia = request.form.get('tipo_garantia')
            contrato.valor_garantia = float(request.form['valor_garantia']) if request.form.get('valor_garantia') else None
            contrato.validade_garantia = parse_date_field(request.form.get('validade_garantia'))
            
            # Observações
            contrato.observacoes = request.form.get('observacoes')
            
            # Processar itens do contrato
            processar_itens_contrato(contrato, request.form)
            
            db.session.commit()
            flash('Contrato atualizado com sucesso!', 'success')
            return redirect(url_for('contratos.detalhes', id=contrato.id))
            
        except ValueError as e:
            flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro ao atualizar contrato: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('contratos/form.html', contrato=contrato)

@contratos_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir(id):
    """Excluir contrato"""
    if request.method == 'GET':
        # Se for GET, redirecionar para a página de contratos
        return redirect(url_for('contratos.index'))
        
    contrato = Contrato.query.get_or_404(id)
    force = request.form.get('force', 'false').lower() == 'true'
    
    try:
        # Verificar se há empenhos vinculados
        empenhos_vinculados = Empenho.query.filter_by(contrato_id=id).count()
        if empenhos_vinculados > 0:
            flash(f'Não é possível excluir o contrato. Há {empenhos_vinculados} empenho(s) vinculado(s).', 'error')
            return redirect(url_for('contratos.index'))
        
        # Verificar se há aditivos vinculados
        aditivos_vinculados = AditivoContratual.query.filter_by(contrato_id=id).count()
        if aditivos_vinculados > 0 and not force:
            flash(f'O contrato possui {aditivos_vinculados} aditivo(s) que serão excluídos automaticamente junto com o contrato. Confirme a exclusão para prosseguir.', 'warning')
            return redirect(url_for('contratos.index'))
        
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
    
    return redirect(url_for('contratos.index'))

@contratos_bp.route('/<int:id>/download')
@login_required
def download_arquivo(id):
    """Download do arquivo do contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    if not contrato.arquivo_contrato:
        flash('Nenhum arquivo disponível para download.', 'error')
        return redirect(url_for('contratos.detalhes', id=id))
    
    import os
    from flask import send_file
    
    arquivo_path = os.path.join(current_app.root_path, 'uploads', 'contratos', contrato.arquivo_contrato)
    
    if not os.path.exists(arquivo_path):
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('contratos.detalhes', id=id))
    
    return send_file(arquivo_path, as_attachment=True)

@contratos_bp.route('/<int:id>/excluir-ajax', methods=['POST'])
@login_required
def excluir_ajax(id):
    """Excluir contrato via AJAX"""
    contrato = Contrato.query.get_or_404(id)
    force = request.json.get('force', False) if request.is_json else request.form.get('force', 'false').lower() == 'true'
    
    try:
        # Verificar se há empenhos vinculados
        empenhos_vinculados = Empenho.query.filter_by(contrato_id=id).count()
        if empenhos_vinculados > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir o contrato. Há {empenhos_vinculados} empenho(s) vinculado(s).'
            })
        
        # Verificar se há aditivos vinculados
        aditivos_vinculados = AditivoContratual.query.filter_by(contrato_id=id).count()
        if aditivos_vinculados > 0 and not force:
            return jsonify({
                'success': False,
                'confirm_needed': True,
                'message': f'O contrato possui {aditivos_vinculados} aditivo(s) que serão excluídos automaticamente.',
                'aditivos_count': aditivos_vinculados
            })
        
        # Se chegou aqui, pode excluir (cascade irá excluir os aditivos automaticamente)
        db.session.delete(contrato)
        db.session.commit()
        
        if aditivos_vinculados > 0:
            message = f'Contrato e {aditivos_vinculados} aditivo(s) excluídos com sucesso!'
        else:
            message = 'Contrato excluído com sucesso!'
            
        return jsonify({
            'success': True,
            'message': message
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir contrato: {str(e)}'
        })

# Rotas para Aditivos Contratuais
@contratos_bp.route('/<int:contrato_id>/aditivos', methods=['GET'])
@login_required
def listar_aditivos(contrato_id):
    """Listar aditivos de um contrato"""
    contrato = Contrato.query.get_or_404(contrato_id)
    aditivos = AditivoContratual.query.filter_by(contrato_id=contrato_id).order_by(AditivoContratual.numero_aditivo).all()
    
    return render_template('contratos/aditivos_list.html', 
                         contrato=contrato, 
                         aditivos=aditivos)

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
                nova_data_fim=parse_date_field(request.form.get('nova_data_fim')),
                data_assinatura=parse_date_field(request.form.get('data_assinatura')) or datetime.now().date(),
                data_publicacao=parse_date_field(request.form.get('data_publicacao')),
                data_inicio_vigencia=parse_date_field(request.form.get('data_inicio_vigencia')),
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
            aditivo.nova_data_fim = parse_date_field(request.form.get('nova_data_fim'))
            aditivo.data_assinatura = parse_date_field(request.form.get('data_assinatura')) or aditivo.data_assinatura
            aditivo.data_publicacao = parse_date_field(request.form.get('data_publicacao'))
            aditivo.data_inicio_vigencia = parse_date_field(request.form.get('data_inicio_vigencia'))
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
        print(f"DEBUG: Dados recebidos: {dict(request.form)}")
        contrato_id = request.form.get('contrato_id')
        print(f"DEBUG: contrato_id = {contrato_id}")
        
        if not contrato_id:
            return jsonify({'success': False, 'error': 'ID do contrato não fornecido'})
            
        contrato = Contrato.query.get_or_404(contrato_id)
        
        # Verificar se o número do aditivo já existe
        numero_aditivo = int(request.form['numero_aditivo'])
        print(f"DEBUG: numero_aditivo = {numero_aditivo}")
        
        aditivo_existente = AditivoContratual.query.filter_by(
            contrato_id=contrato_id, 
            numero_aditivo=numero_aditivo
        ).first()
        
        if aditivo_existente:
            print(f"DEBUG: Aditivo {numero_aditivo} já existe para contrato {contrato_id}")
            return jsonify({
                'success': False,
                'error': f'{numero_aditivo}° Termo Aditivo já existe para este contrato.'
            })
        
        # Criar novo aditivo
        print(f"DEBUG: Criando aditivo...")
        aditivo = AditivoContratual(
            contrato_id=contrato_id,
            numero_aditivo=numero_aditivo,
            tipo=request.form['tipo'],
            data_assinatura=datetime.strptime(request.form['data_aditivo'], '%Y-%m-%d').date(),
            justificativa=request.form['justificativa']
        )
        print(f"DEBUG: Aditivo criado: {aditivo}")
        
        # Campos opcionais
        if request.form.get('valor_financeiro'):
            aditivo.valor_financeiro = float(request.form['valor_financeiro'])
            print(f"DEBUG: valor_financeiro = {aditivo.valor_financeiro}")
        
        if request.form.get('prazo_dias'):
            aditivo.prazo_prorrogacao = int(request.form['prazo_dias'])
            print(f"DEBUG: prazo_prorrogacao = {aditivo.prazo_prorrogacao}")
        
        if request.form.get('nova_data_fim'):
            aditivo.nova_data_fim = datetime.strptime(request.form['nova_data_fim'], '%Y-%m-%d').date()
            # Atualizar data_fim do contrato se fornecida
            contrato.data_fim = aditivo.nova_data_fim
            print(f"DEBUG: nova_data_fim = {aditivo.nova_data_fim}")

        print(f"DEBUG: Adicionando aditivo à sessão...")
        db.session.add(aditivo)
        print(f"DEBUG: Fazendo commit...")
        db.session.commit()
        print(f"DEBUG: Commit realizado com sucesso!")
        
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


def processar_itens_contrato(contrato, form_data):
    """Processa os itens do contrato enviados pelo formulário"""
    # Primeiro, remover itens existentes se for edição
    if contrato.id:
        ItemContrato.query.filter_by(contrato_id=contrato.id).delete()
    
    # Processar novos itens
    index = 0
    while f'itens[{index}][item]' in form_data:
        item_data = {
            'lote': form_data.get(f'itens[{index}][lote]', ''),
            'item': form_data.get(f'itens[{index}][item]'),
            'descricao': form_data.get(f'itens[{index}][descricao]'),
            'marca': form_data.get(f'itens[{index}][marca]', ''),
            'quantidade': form_data.get(f'itens[{index}][quantidade]'),
            'unidade': form_data.get(f'itens[{index}][unidade]'),
            'valor_unitario': form_data.get(f'itens[{index}][valor_unitario]'),
        }
        
        # Validar dados obrigatórios
        if not all([item_data['item'], item_data['descricao'], 
                   item_data['quantidade'], item_data['unidade'], 
                   item_data['valor_unitario']]):
            index += 1
            continue
        
        try:
            # Criar item
            item = ItemContrato(
                contrato_id=contrato.id,
                lote=item_data['lote'] or None,
                item=item_data['item'],
                descricao=item_data['descricao'],
                marca=item_data['marca'] or None,
                quantidade=float(item_data['quantidade']),
                unidade=item_data['unidade'],
                valor_unitario=float(item_data['valor_unitario'])
            )
            
            # Calcular valor total automaticamente
            item.calcular_valor_total()
            
            db.session.add(item)
            
        except (ValueError, TypeError) as e:
            # Pular item com dados inválidos
            current_app.logger.warning(f'Item inválido ignorado: {str(e)}')
            pass
        
        index += 1

# Rotas para Anotações de Contratos
@contratos_bp.route('/<int:contrato_id>/anotacoes', methods=['GET'])
@login_required
def listar_anotacoes(contrato_id):
    """Listar anotações de um contrato via AJAX"""
    contrato = Contrato.query.get_or_404(contrato_id)
    anotacoes = (AnotacaoContrato.query
                 .filter_by(contrato_id=contrato_id)
                 .order_by(AnotacaoContrato.data_criacao.desc())
                 .all())

    out = []
    for a in anotacoes:
        d = a.to_dict() if hasattr(a, 'to_dict') else {}
        d.update({
            'id': a.id,
            'texto': a.texto,
            'usuario': getattr(a.usuario, 'nome', 'Usuário'),
            'data_criacao': (a.data_criacao.isoformat() if a.data_criacao else None)  # ISO 8601
        })
        d['anexos'] = [x.to_dict() if hasattr(x, 'to_dict') else {
            'id': x.id,
            'nome': x.nome,
            'mimetype': x.tipo,
            'tipo': x.tipo,
            'tamanho': x.tamanho,
            'created_at': (x.data_upload.isoformat() if x.data_upload else None)
        } for x in a.anexos]
        out.append(d)

    return jsonify({'success': True, 'anotacoes': out})

@contratos_bp.route('/<int:contrato_id>/anotacoes', methods=['POST'])
@login_required
def criar_anotacao(contrato_id):
    """Criar nova anotação para um contrato"""
    contrato = Contrato.query.get_or_404(contrato_id)
    
    try:
        # Obter dados do formulário
        texto = request.form.get('texto', '').strip()
        
        if not texto:
            return jsonify({
                'success': False,
                'error': 'Texto da anotação é obrigatório'
            }), 400
        
        # Criar nova anotação
        anotacao = AnotacaoContrato(
            contrato_id=contrato_id,
            usuario_id=current_user.id,
            texto=texto
        )
        
        # Salvar anotação primeiro para obter o ID
        db.session.add(anotacao)
        db.session.flush()  # Para obter o ID sem fazer commit completo
        
        # Processar múltiplos arquivos
        arquivos = request.files.getlist('arquivos')
        anexos_salvos = []
        
        print(f"🔍 DEBUG: Arquivos recebidos: {len(arquivos)}")
        for i, arquivo in enumerate(arquivos):
            print(f"🔍 DEBUG: Arquivo {i}: {arquivo.filename if arquivo else 'None'}")
        
        if arquivos and any(arquivo.filename for arquivo in arquivos):
            import os
            from werkzeug.utils import secure_filename
            
            # Configurar diretório de upload
            upload_dir = os.path.join(current_app.instance_path, 'uploads', 'anotacoes')
            os.makedirs(upload_dir, exist_ok=True)
            print(f"🔍 DEBUG: Upload dir: {upload_dir}")
            
            for arquivo in arquivos:
                if arquivo and arquivo.filename:
                    print(f"🔍 DEBUG: Processando arquivo: {arquivo.filename}")
                    # Salvar arquivo
                    filename = secure_filename(arquivo.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename_final = timestamp + filename
                    caminho_arquivo = os.path.join(upload_dir, filename_final)
                    arquivo.save(caminho_arquivo)
                    print(f"🔍 DEBUG: Arquivo salvo em: {caminho_arquivo}")
                    
                    # Criar registro do anexo
                    anexo = AnexoAnotacao(
                        anotacao_id=anotacao.id,
                        nome=arquivo.filename,  # Nome original
                        caminho=caminho_arquivo,  # Caminho no servidor
                        tamanho=os.path.getsize(caminho_arquivo),
                        tipo=arquivo.content_type,
                        data_upload=datetime.now()
                    )
                    
                    db.session.add(anexo)
                    anexos_salvos.append(anexo.to_dict())
                    print(f"🔍 DEBUG: Anexo criado: {anexo.to_dict()}")
        else:
            print(f"🔍 DEBUG: Nenhum arquivo válido encontrado")
        
        db.session.commit()
        
        # Retornar dados em formato consistente (ISO 8601 para datas)
        anotacao_dict = {
            'id': anotacao.id,
            'texto': anotacao.texto,
            'usuario': getattr(anotacao.usuario, 'nome', 'Usuário'),
            'data_criacao': anotacao.data_criacao.isoformat() if anotacao.data_criacao else None,
            'data_atualizacao': (
                anotacao.data_atualizacao.isoformat()
                if getattr(anotacao, 'data_atualizacao', None) else None
            ),
            'anexos': anexos_salvos
        }
        
        return jsonify({
            'success': True,
            'message': 'Anotação criada com sucesso',
            'anotacao': anotacao_dict
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao criar anotação: {str(e)}'
        }), 500

@contratos_bp.route('/anotacoes/<int:anotacao_id>', methods=['DELETE'])
@login_required
def excluir_anotacao(anotacao_id):
    """Excluir uma anotação"""
    anotacao = AnotacaoContrato.query.get_or_404(anotacao_id)
    
    # Verificar se o usuário pode excluir (criador ou admin)
    if anotacao.usuario_id != current_user.id and not current_user.is_admin:
        return jsonify({
            'success': False,
            'error': 'Você não tem permissão para excluir esta anotação'
        }), 403
    
    try:
        import os
        
        # Remover anexos individuais (nova implementação)
        for anexo in anotacao.anexos:
            if anexo.caminho and os.path.exists(anexo.caminho):
                os.remove(anexo.caminho)
        
        # Remover arquivo antigo se existir (compatibilidade)
        if hasattr(anotacao, 'caminho_arquivo') and anotacao.caminho_arquivo and os.path.exists(anotacao.caminho_arquivo):
            os.remove(anotacao.caminho_arquivo)
        
        # Deletar anotação (anexos são deletados em cascata)
        db.session.delete(anotacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Anotação excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir anotação: {str(e)}'
        }), 500

@contratos_bp.route('/anexos/<int:anexo_id>')
@login_required
def anexo(anexo_id):
    """Rota padrão para anexos - redireciona para download"""
    return download_anexo(anexo_id)

@contratos_bp.route('/anexos/<int:anexo_id>/download')
@login_required
def download_anexo(anexo_id):
    """Download de um anexo específico"""
    anexo = AnexoAnotacao.query.get_or_404(anexo_id)
    
    try:
        import os
        from flask import send_file
        
        if not anexo.caminho or not os.path.exists(anexo.caminho):
            return jsonify({
                'success': False,
                'error': 'Arquivo não encontrado'
            }), 404
        
        return send_file(
            anexo.caminho,
            as_attachment=True,
            download_name=anexo.nome,
            mimetype=anexo.tipo
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao baixar arquivo: {str(e)}'
        }), 500

@contratos_bp.route('/anexos/<int:anexo_id>/inline')
@login_required
def visualizar_anexo_inline(anexo_id):
    """Visualizar anexo inline (para iframes/navegador)"""
    anexo = AnexoAnotacao.query.get_or_404(anexo_id)
    
    try:
        import os
        import mimetypes
        from flask import send_file, abort
        
        if not anexo.caminho or not os.path.exists(anexo.caminho):
            abort(404)
        
        # Determinar mimetype correto
        if anexo.caminho.lower().endswith('.pdf'):
            mime = "application/pdf"
        else:
            mime = mimetypes.guess_type(anexo.caminho)[0] or "application/octet-stream"
        
        # IMPORTANTE: as_attachment=False, Content-Disposition inline e conditional=True
        resp = send_file(
            anexo.caminho,
            mimetype=mime,
            as_attachment=False,
            download_name=anexo.nome,
            conditional=True,  # permite "Range" (melhor para players/iframes)
        )
        
        # Definir headers corretos para visualização inline
        resp.headers["Content-Disposition"] = f'inline; filename="{anexo.nome}"'
        # Liberar X-Frame-Options para same-origin (permite iframe)
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        return resp
        
    except Exception as e:
        abort(500)


# ===== NOVOS ENDPOINTS PARA O SISTEMA DE UPLOAD PROFISSIONAL =====

# ===== ROTA UNIFICADA PARA ANEXOS (GET/POST) =====

@contratos_bp.route('/<int:contrato_id>/anexos', methods=['GET', 'POST'])
@login_required
def anexos_crud(contrato_id):
    """Rota unificada para listar (GET) e fazer upload (POST) de anexos"""
    
    if request.method == 'GET':
        # LISTAR ANEXOS
        print(f"[DEBUG] GET anexos para contrato {contrato_id}")
        anexos = (
            db.session.query(AnexoAnotacao)
            .join(AnotacaoContrato, AnexoAnotacao.anotacao_id == AnotacaoContrato.id)
            .filter(AnotacaoContrato.contrato_id == contrato_id)
            .order_by(AnexoAnotacao.data_upload.desc())
            .all()
        )
        
        result = {
            'success': True,
            'anexos': [{
                'id': a.id,
                'nome': a.nome,
                'mimetype': a.tipo,  # alias que o JS entende
                'tipo': a.tipo,
                'tamanho': a.tamanho,
                'data_upload': a.data_upload.isoformat() if a.data_upload else None  # ISO 8601
            } for a in anexos]
        }
        
        print(f"[DEBUG] Retornando {len(anexos)} anexos")
        return jsonify(result)

    # POST (UPLOAD)
    print(f"[DEBUG] POST upload para contrato {contrato_id}")
    
    if 'arquivo' not in request.files or not request.files['arquivo'].filename:
        return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400

    arquivo = request.files['arquivo']

    from werkzeug.utils import secure_filename
    import mimetypes

    upload_dir = os.path.join(current_app.instance_path, 'uploads', 'anotacoes')
    os.makedirs(upload_dir, exist_ok=True)
    safe = secure_filename(arquivo.filename)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S_')
    filename = ts + safe
    path = os.path.join(upload_dir, filename)
    arquivo.save(path)

    # Garante uma anotação "container" para anexos
    anotacao = (AnotacaoContrato.query
                .filter_by(contrato_id=contrato_id)
                .order_by(AnotacaoContrato.id.desc()).first())
    if not anotacao:
        anotacao = AnotacaoContrato(
            contrato_id=contrato_id,
            usuario_id=current_user.id,
            texto='Anexos do contrato',
            data_criacao=datetime.utcnow()
        )
        db.session.add(anotacao)
        db.session.flush()

    anexo = AnexoAnotacao(
        anotacao_id=anotacao.id,
        nome=safe,
        caminho=path,
        tamanho=os.path.getsize(path),
        tipo=mimetypes.guess_type(path)[0] or 'application/octet-stream',
        data_upload=datetime.utcnow()
    )
    db.session.add(anexo)
    db.session.commit()

    print(f"[DEBUG] Anexo {anexo.id} salvo: {anexo.nome}")

    return jsonify({
        'success': True,
        'anexo_id': anexo.id,
        'filename': anexo.nome,
        'size': anexo.tamanho
    })


@contratos_bp.route('/anexos/<int:anexo_id>', methods=['DELETE'])
@login_required
def excluir_anexo(anexo_id):
    """Excluir anexo específico"""
    try:
        print(f"[EXCLUIR] Excluindo anexo {anexo_id}")
        
        anexo = AnexoAnotacao.query.get_or_404(anexo_id)
        
        db.session.delete(anexo)
        db.session.commit()
        
        print(f"[EXCLUIR] Anexo {anexo_id} excluído com sucesso")
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"[EXCLUIR] Erro: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@contratos_bp.route('/importar-excel', methods=['POST'])
@login_required
def importar_excel():
    """Importar itens de contrato a partir de arquivo Excel"""
    try:
        if 'arquivo_excel' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo foi enviado'})
        
        file = request.files['arquivo_excel']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo foi selecionado'})
        
        # Verificar extensão do arquivo
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Formato de arquivo inválido. Use apenas .xlsx ou .xls'})
        
        # Importar bibliotecas necessárias
        import pandas as pd
        from io import BytesIO
        
        # Ler o arquivo Excel
        file_content = file.read()
        file_io = BytesIO(file_content)
        
        try:
            # Tentar ler como xlsx primeiro
            df = pd.read_excel(file_io, engine='openpyxl')
        except:
            try:
                # Se falhar, tentar como xls
                file_io.seek(0)
                df = pd.read_excel(file_io, engine='xlrd')
            except Exception as e:
                return jsonify({'success': False, 'error': f'Erro ao ler arquivo Excel: {str(e)}'})
        
        # Verificar se o DataFrame não está vazio
        if df.empty:
            return jsonify({'success': False, 'error': 'O arquivo Excel está vazio'})
        
        # Mapear colunas esperadas (flexível com diferentes nomes)
        column_mapping = {
            'lote': ['lote', 'LOTE', 'Lote', 'lote_num', 'numero_lote'],
            'item': ['item', 'ITEM', 'Item', 'codigo', 'codigo_item', 'number', 'num'],
            'descricao': ['descricao', 'DESCRIÇÃO', 'Descrição', 'description', 'produto', 'servico'],
            'marca': ['marca', 'MARCA', 'Marca', 'brand', 'fabricante'],
            'unidade': ['unidade', 'UNIDADE', 'Unidade', 'un', 'UN', 'unit'],
            'quantidade': ['quantidade', 'QUANTIDADE', 'Quantidade', 'qty', 'qtd', 'qtde'],
            'valor_unitario': ['valor_unitario', 'VALOR UNITÁRIO', 'Valor Unitário', 'valor_unit', 'preco', 'price', 'unit_price']
        }
        
        # Função para encontrar coluna correspondente
        def find_column(df_columns, possible_names):
            for name in possible_names:
                if name in df_columns:
                    return name
            return None
        
        # Mapear colunas reais
        mapped_columns = {}
        for field, possible_names in column_mapping.items():
            found_column = find_column(df.columns, possible_names)
            if found_column:
                mapped_columns[field] = found_column
        
        # Verificar se encontramos pelo menos as colunas obrigatórias
        required_fields = ['item', 'descricao', 'quantidade', 'valor_unitario']
        missing_fields = [field for field in required_fields if field not in mapped_columns]
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Colunas obrigatórias não encontradas: {", ".join(missing_fields)}. '
                        f'Colunas disponíveis: {", ".join(df.columns.tolist())}'
            })
        
        # Processar dados
        itens_importados = []
        
        for index, row in df.iterrows():
            try:
                # Extrair dados da linha
                item_data = {}
                
                for field, column in mapped_columns.items():
                    value = row[column]
                    # Tratar valores NaN
                    if pd.isna(value):
                        item_data[field] = '' if field in ['lote', 'marca'] else None
                    else:
                        item_data[field] = str(value).strip()
                
                # Validar dados obrigatórios
                if not all([item_data.get('item'), item_data.get('descricao'), 
                           item_data.get('quantidade'), item_data.get('valor_unitario')]):
                    continue  # Pular linha com dados incompletos
                
                # Converter valores numéricos
                try:
                    item_data['quantidade'] = float(str(item_data['quantidade']).replace(',', '.'))
                    item_data['valor_unitario'] = float(str(item_data['valor_unitario']).replace(',', '.'))
                except (ValueError, TypeError):
                    continue  # Pular linha com valores inválidos
                
                # Normalizar unidade se não especificada
                if not item_data.get('unidade'):
                    item_data['unidade'] = 'UN'
                
                itens_importados.append(item_data)
                
            except Exception as e:
                current_app.logger.warning(f'Erro ao processar linha {index + 1}: {str(e)}')
                continue
        
        if not itens_importados:
            return jsonify({'success': False, 'error': 'Nenhum item válido foi encontrado no arquivo'})
        
        return jsonify({
            'success': True,
            'itens': itens_importados,
            'total': len(itens_importados)
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao importar Excel: {str(e)}')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'})
