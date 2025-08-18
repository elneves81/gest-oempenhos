# routes/contratos_robust.py
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, send_from_directory, abort
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models import db, Contrato

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

ALLOWED_EXTS = {'pdf', 'doc', 'docx'}
MAX_UPLOAD_MB = 10

def parse_money(name):
    """Parse valor monetário de forma segura"""
    val = (request.form.get(name) or '').strip()
    if val == '':
        return None
    try:
        # Tratar vírgula decimal brasileira
        val = val.replace(',', '.')
        return Decimal(val)
    except InvalidOperation:
        flash(f'Valor inválido no campo {name}', 'warning')
        return None

def parse_date(name):
    """Parse data de forma segura"""
    s = (request.form.get(name) or '').strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        flash(f'Data inválida no campo {name}', 'warning')
        return None

def parse_int(name):
    """Parse inteiro de forma segura"""
    val = (request.form.get(name) or '').strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        flash(f'Número inválido no campo {name}', 'warning')
        return None

@contratos_bp.route('/')
def index():
    """Listar contratos"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = Contrato.query.order_by(Contrato.data_criacao.desc())
    contratos = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('contratos/index.html', contratos=contratos)

@contratos_bp.route('/novo')
def novo():
    """Formulário para novo contrato"""
    return render_template('contratos/form_novo.html', contrato=None)

@contratos_bp.route('/novo', methods=['POST'])
def criar():
    """Criar novo contrato"""
    return _salvar_contrato()

@contratos_bp.route('/<int:id>/editar')
def editar(id):
    """Formulário para editar contrato"""
    contrato = Contrato.query.get_or_404(id)
    return render_template('contratos/form_novo.html', contrato=contrato)

@contratos_bp.route('/<int:id>/editar', methods=['POST'])
def atualizar(id):
    """Atualizar contrato existente"""
    return _salvar_contrato(id)

@contratos_bp.route('/<int:id>')
def detalhes(id):
    """Ver detalhes do contrato"""
    contrato = Contrato.query.get_or_404(id)
    return render_template('contratos/detalhes.html', contrato=contrato)

def _salvar_contrato(id=None):
    """Lógica compartilhada para criar/atualizar contrato"""
    contrato = Contrato.query.get_or_404(id) if id else Contrato()
    
    # Validar campos obrigatórios
    obrigatorios = ['numero_contrato', 'objeto', 'fornecedor', 'valor_total', 
                   'data_assinatura', 'data_inicio', 'data_fim']
    faltando = []
    
    for campo in obrigatorios:
        valor = (request.form.get(campo) or '').strip()
        if not valor:
            faltando.append(campo.replace('_', ' ').title())
    
    if faltando:
        flash(f'Campos obrigatórios não preenchidos: {", ".join(faltando)}', 'warning')
        return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
    
    # Atribuições básicas
    contrato.numero_pregao = request.form.get('numero_pregao') or None
    contrato.numero_contrato = request.form.get('numero_contrato') or None
    contrato.numero_processo = request.form.get('numero_processo') or None
    
    # Anos
    contrato.ano_pregao = parse_int('ano_pregao')
    contrato.ano_contrato = parse_int('ano_contrato')
    contrato.ano_processo = parse_int('ano_processo')
    
    # Texto
    contrato.objeto = request.form.get('objeto') or None
    contrato.lei_base = request.form.get('lei_base') or None
    contrato.modalidade_licitacao = request.form.get('modalidade_licitacao') or None
    contrato.orgao_contratante = request.form.get('orgao_contratante') or None
    contrato.secretaria = request.form.get('secretaria') or None
    
    # Fornecedor
    contrato.fornecedor = request.form.get('fornecedor') or None
    cnpj_raw = request.form.get('cnpj_fornecedor') or ''
    contrato.cnpj_fornecedor = cnpj_raw.strip() if cnpj_raw.strip() else None
    
    # Responsável
    contrato.responsavel_nome = request.form.get('responsavel_nome') or None
    contrato.responsavel_cargo = request.form.get('responsavel_cargo') or None
    contrato.responsavel_email = request.form.get('responsavel_email') or None
    contrato.responsavel_telefone = request.form.get('responsavel_telefone') or None
    
    # Valores monetários
    contrato.valor_total = parse_money('valor_total')
    contrato.valor_inicial = parse_money('valor_inicial')
    
    # Datas
    contrato.data_assinatura = parse_date('data_assinatura')
    contrato.data_inicio = parse_date('data_inicio')
    contrato.data_fim = parse_date('data_fim')
    contrato.data_fim_original = parse_date('data_fim_original')
    
    # Gestores
    contrato.gestor_fiscal = request.form.get('gestor_fiscal') or None
    contrato.gestor_superior = request.form.get('gestor_superior') or None
    
    # Garantias
    contrato.tipo_garantia = request.form.get('tipo_garantia') or None
    contrato.valor_garantia = parse_money('valor_garantia')
    contrato.validade_garantia = parse_date('validade_garantia')
    
    # Observações
    contrato.observacoes = request.form.get('observacoes') or None
    
    # Validações adicionais
    if contrato.data_fim and contrato.data_inicio and contrato.data_fim <= contrato.data_inicio:
        flash('A data de fim deve ser posterior à data de início.', 'warning')
        return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
    
    # Validar CNPJ se preenchido
    if contrato.cnpj_fornecedor:
        cnpj_digits = ''.join(filter(str.isdigit, contrato.cnpj_fornecedor))
        if len(cnpj_digits) != 14:
            flash('CNPJ deve ter exatamente 14 dígitos.', 'warning')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
    
    # Validar email se preenchido
    if contrato.responsavel_email:
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, contrato.responsavel_email):
            flash('Email do responsável inválido.', 'warning')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
    
    # Upload de arquivo
    file = request.files.get('arquivo_contrato')
    if file and file.filename:
        filename = secure_filename(file.filename)
        if not filename:
            flash('Nome de arquivo inválido.', 'warning')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
            
        # Verificar extensão
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTS:
            flash('Arquivo inválido. Envie apenas PDF, DOC ou DOCX.', 'warning')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
        
        # Verificar tamanho
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        
        if size_mb > MAX_UPLOAD_MB:
            flash(f'Arquivo excede {MAX_UPLOAD_MB} MB.', 'warning')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 400
        
        # Salvar arquivo
        upload_dir = os.path.join(current_app.instance_path, 'uploads', 'contratos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Nome único para o arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_final = f"{timestamp}_{filename}"
        path = os.path.join(upload_dir, nome_final)
        
        try:
            file.save(path)
            contrato.arquivo_contrato = nome_final
        except Exception as e:
            flash('Erro ao salvar arquivo. Tente novamente.', 'danger')
            current_app.logger.error(f'Erro ao salvar arquivo: {e}')
            return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 500
    
    # Persistir no banco
    try:
        if not id:
            contrato.data_criacao = datetime.now()
            db.session.add(contrato)
        else:
            contrato.data_atualizacao = datetime.now()
        
        db.session.commit()
        
        action = 'atualizado' if id else 'criado'
        flash(f'Contrato {action} com sucesso!', 'success')
        return redirect(url_for('contratos.detalhes', id=contrato.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao salvar contrato. Tente novamente.', 'danger')
        current_app.logger.error(f'Erro ao salvar contrato: {e}')
        return render_template('contratos/form_novo.html', contrato=(contrato if id else None)), 500

@contratos_bp.route('/<int:id>/download')
def download_arquivo(id):
    """Download do arquivo do contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    if not contrato.arquivo_contrato:
        flash('Arquivo não encontrado.', 'warning')
        return redirect(url_for('contratos.detalhes', id=id))
    
    upload_dir = os.path.join(current_app.instance_path, 'uploads', 'contratos')
    arquivo_path = os.path.join(upload_dir, contrato.arquivo_contrato)
    
    if not os.path.exists(arquivo_path):
        flash('Arquivo não encontrado no servidor.', 'warning')
        return redirect(url_for('contratos.detalhes', id=id))
    
    return send_from_directory(upload_dir, contrato.arquivo_contrato, as_attachment=True)

@contratos_bp.route('/<int:id>/deletar', methods=['POST'])
def deletar(id):
    """Deletar contrato"""
    contrato = Contrato.query.get_or_404(id)
    
    try:
        # Remover arquivo se existir
        if contrato.arquivo_contrato:
            upload_dir = os.path.join(current_app.instance_path, 'uploads', 'contratos')
            arquivo_path = os.path.join(upload_dir, contrato.arquivo_contrato)
            if os.path.exists(arquivo_path):
                os.remove(arquivo_path)
        
        db.session.delete(contrato)
        db.session.commit()
        
        flash('Contrato excluído com sucesso!', 'success')
        return redirect(url_for('contratos.index'))
        
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir contrato.', 'danger')
        current_app.logger.error(f'Erro ao excluir contrato: {e}')
        return redirect(url_for('contratos.detalhes', id=id))
