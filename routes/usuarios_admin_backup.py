"""
Blueprint para Gerenciamento de Usuários e Departamentos
Sistema completo de administração departamental
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import json

usuarios_admin_bp = Blueprint('usuarios_admin', __name__)

# Função para importar modelos (evita importação circular)
def get_models():
    from app_mysql_principal import db, User, Departamento
    return db, User, Departamento

def require_admin():
    """Decorator para verificar se usuário é admin"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Login necessário', 'error')
                return redirect(url_for('login'))
            
            # Verificar se é admin - múltiplas verificações para garantir
            is_admin = (
                current_user.username == 'admin' or 
                (hasattr(current_user, 'role') and current_user.role == 'ADMIN') or
                (hasattr(current_user, 'is_admin') and current_user.is_admin)
            )
            
            if not is_admin:
                flash('Acesso negado - apenas administradores podem acessar esta área', 'error')
                return redirect(url_for('painel'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_coordenador_ou_admin():
    """Decorator para verificar se usuário é coordenador ou admin"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'error': 'Login necessário'}), 401
            
            if not (hasattr(current_user, 'is_coordenador') and current_user.is_coordenador):
                return jsonify({'success': False, 'error': 'Acesso negado - apenas coordenadores'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@usuarios_admin_bp.route('/')
@login_required
@require_admin()
def index():
    """Página principal de administração"""
    try:
        db, User, Departamento = get_models()
        
        # Estatísticas gerais
        total_usuarios = User.query.count()
        usuarios_ativos = User.query.filter_by(ativo=True).count()
        total_departamentos = Departamento.query.count()
        departamentos_ativos = Departamento.query.filter_by(ativo=True).count()
        
        # Usuários recentes
        usuarios_recentes = User.query.order_by(User.data_criacao.desc()).limit(5).all()
        
        # Departamentos com mais usuários (usando contagem simples)
        departamentos = Departamento.query.limit(5).all()
        
        estatisticas = {
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'usuarios_inativos': total_usuarios - usuarios_ativos,
            'total_departamentos': total_departamentos,
            'departamentos_ativos': departamentos_ativos,
            'usuarios_recentes': [
                {
                    'id': u.id,
                    'username': u.username,
                    'nome_completo': getattr(u, 'nome_completo', ''),
                    'email': u.email,
                    'data_criacao': u.data_criacao.strftime('%d/%m/%Y') if u.data_criacao else ''
                } for u in usuarios_recentes
            ],
            'departamentos_principais': [
                {
                    'id': d.id,
                    'nome': d.nome,
                    'codigo': d.codigo,
                    'tipo': d.tipo
                } for d in departamentos
            ]
        }
        
        return render_template('admin/usuarios/index.html', estatisticas=estatisticas)
        
    except Exception as e:
        flash(f'Erro ao carregar página de administração: {str(e)}', 'error')
        return redirect(url_for('painel'))

# ============================================================================
# GESTÃO DE DEPARTAMENTOS
# ============================================================================

@usuarios_admin_bp.route('/departamentos')
@login_required
@require_admin()
def listar_departamentos():
    """Lista todos os departamentos"""
    try:
        db, User, Departamento = get_models()
        
        # Parâmetros de filtro
        busca = request.args.get('busca', '')
        tipo = request.args.get('tipo', '')
        ativo = request.args.get('ativo', '')
        
        # Query base
        query = Departamento.query
        
        # Aplicar filtros
        if busca:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Departamento.nome.ilike(f'%{busca}%'),
                    Departamento.codigo.ilike(f'%{busca}%'),
                    Departamento.descricao.ilike(f'%{busca}%')
                )
            )
        
        if tipo:
            query = query.filter(Departamento.tipo == tipo)
        
        if ativo:
            query = query.filter(Departamento.ativo == (ativo.lower() == 'true'))
        
        # Ordenação
        departamentos = query.order_by(
            Departamento.nivel_hierarquia.asc(),
            Departamento.nome.asc()
        ).all()
        
        # Árvore hierárquica
        arvore_departamentos = Departamento.get_departamentos_tree()
        
        return render_template(
            'admin/usuarios/departamentos.html',
            departamentos=departamentos,
            arvore_departamentos=arvore_departamentos,
            filtros={'busca': busca, 'tipo': tipo, 'ativo': ativo}
        )
        
    except Exception as e:
        flash(f'Erro ao listar departamentos: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.index'))

@usuarios_admin_bp.route('/departamentos/novo', methods=['GET', 'POST'])
@login_required
@require_admin()
def novo_departamento():
    """Criar novo departamento"""
    if request.method == 'GET':
        try:
            from models.departamento import Departamento
            
            # Departamentos pais disponíveis
            departamentos_pais = Departamento.query.filter_by(ativo=True).all()
            
            return render_template(
                'admin/usuarios/departamento_form.html',
                departamentos_pais=departamentos_pais,
                departamento=None
            )
            
        except Exception as e:
            flash(f'Erro ao carregar formulário: {str(e)}', 'error')
            return redirect(url_for('usuarios_admin.listar_departamentos'))
    
    # POST - Criar departamento
    try:
        from app_mysql_principal import db
        from models.departamento import Departamento
        
        # Validar dados obrigatórios
        codigo = request.form.get('codigo', '').strip().upper()
        nome = request.form.get('nome', '').strip()
        
        if not codigo or not nome:
            flash('Código e nome são obrigatórios', 'error')
            return redirect(url_for('usuarios_admin.novo_departamento'))
        
        # Verificar se código já existe
        if Departamento.query.filter_by(codigo=codigo).first():
            flash(f'Código "{codigo}" já existe', 'error')
            return redirect(url_for('usuarios_admin.novo_departamento'))
        
        # Criar departamento
        departamento = Departamento(
            codigo=codigo,
            nome=nome,
            descricao=request.form.get('descricao', ''),
            tipo=request.form.get('tipo', 'ADMINISTRATIVO'),
            nivel_hierarquia=int(request.form.get('nivel_hierarquia', 2)),
            departamento_pai_id=request.form.get('departamento_pai_id') or None,
            responsavel_nome=request.form.get('responsavel_nome', ''),
            responsavel_email=request.form.get('responsavel_email', ''),
            responsavel_telefone=request.form.get('responsavel_telefone', ''),
            permite_visualizar_outros=bool(request.form.get('permite_visualizar_outros')),
            permite_gerar_relatorios=bool(request.form.get('permite_gerar_relatorios', True)),
            limite_usuarios=int(request.form.get('limite_usuarios', 10)),
            ativo=bool(request.form.get('ativo', True)),
            criado_por=current_user.id
        )
        
        db.session.add(departamento)
        db.session.commit()
        
        flash(f'Departamento "{nome}" criado com sucesso!', 'success')
        return redirect(url_for('usuarios_admin.listar_departamentos'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar departamento: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.novo_departamento'))

@usuarios_admin_bp.route('/departamentos/<int:departamento_id>/editar', methods=['GET', 'POST'])
@login_required
@require_admin()
def editar_departamento(departamento_id):
    """Editar departamento existente"""
    try:
        from app_mysql_principal import db
        from models.departamento import Departamento
        
        departamento = Departamento.query.get_or_404(departamento_id)
        
        if request.method == 'GET':
            # Departamentos pais disponíveis (excluindo o próprio e seus filhos)
            departamentos_pais = Departamento.query.filter(
                Departamento.id != departamento.id,
                Departamento.ativo == True
            ).all()
            
            # Remover descendentes para evitar loops
            descendentes_ids = [sub.id for sub in departamento.get_todos_subdepartamentos()]
            departamentos_pais = [d for d in departamentos_pais if d.id not in descendentes_ids]
            
            return render_template(
                'admin/usuarios/departamento_form.html',
                departamentos_pais=departamentos_pais,
                departamento=departamento
            )
        
        # POST - Atualizar departamento
        # Validar dados obrigatórios
        codigo = request.form.get('codigo', '').strip().upper()
        nome = request.form.get('nome', '').strip()
        
        if not codigo or not nome:
            flash('Código e nome são obrigatórios', 'error')
            return redirect(url_for('usuarios_admin.editar_departamento', departamento_id=departamento_id))
        
        # Verificar se código já existe (exceto o próprio)
        codigo_existente = Departamento.query.filter(
            Departamento.codigo == codigo,
            Departamento.id != departamento.id
        ).first()
        
        if codigo_existente:
            flash(f'Código "{codigo}" já existe', 'error')
            return redirect(url_for('usuarios_admin.editar_departamento', departamento_id=departamento_id))
        
        # Atualizar dados
        departamento.codigo = codigo
        departamento.nome = nome
        departamento.descricao = request.form.get('descricao', '')
        departamento.tipo = request.form.get('tipo', 'ADMINISTRATIVO')
        departamento.nivel_hierarquia = int(request.form.get('nivel_hierarquia', 2))
        departamento.departamento_pai_id = request.form.get('departamento_pai_id') or None
        departamento.responsavel_nome = request.form.get('responsavel_nome', '')
        departamento.responsavel_email = request.form.get('responsavel_email', '')
        departamento.responsavel_telefone = request.form.get('responsavel_telefone', '')
        departamento.permite_visualizar_outros = bool(request.form.get('permite_visualizar_outros'))
        departamento.permite_gerar_relatorios = bool(request.form.get('permite_gerar_relatorios', True))
        departamento.limite_usuarios = int(request.form.get('limite_usuarios', 10))
        departamento.ativo = bool(request.form.get('ativo', True))
        
        db.session.commit()
        
        flash(f'Departamento "{nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('usuarios_admin.listar_departamentos'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao editar departamento: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.listar_departamentos'))

@usuarios_admin_bp.route('/departamentos/<int:departamento_id>/excluir', methods=['POST'])
@login_required
@require_admin()
def excluir_departamento(departamento_id):
    """Excluir departamento (desativar)"""
    try:
        from app_mysql_principal import db
        from models.departamento import Departamento
        
        departamento = Departamento.query.get_or_404(departamento_id)
        
        # Verificar se tem usuários ativos
        usuarios_ativos = departamento.usuarios.filter_by(ativo=True).count()
        if usuarios_ativos > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir. Departamento possui {usuarios_ativos} usuários ativos.'
            }), 400
        
        # Verificar se tem subdepartamentos ativos
        subdepartamentos_ativos = len([sub for sub in departamento.subdepartamentos if sub.ativo])
        if subdepartamentos_ativos > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir. Departamento possui {subdepartamentos_ativos} subdepartamentos ativos.'
            }), 400
        
        # Desativar departamento
        departamento.ativo = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Departamento "{departamento.nome}" desativado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir departamento: {str(e)}'
        }), 500

# ============================================================================
# GESTÃO DE USUÁRIOS
# ============================================================================

@usuarios_admin_bp.route('/usuarios')
@login_required
@require_coordenador_ou_admin()
def listar_usuarios():
    """Lista usuários (admin vê todos, coordenador vê do seu departamento)"""
    try:
        from models.user_departamental import User
        from models.departamento import Departamento
        
        # Parâmetros de filtro
        busca = request.args.get('busca', '')
        departamento_id = request.args.get('departamento_id', '')
        role = request.args.get('role', '')
        ativo = request.args.get('ativo', '')
        
        # Query base - filtrar por permissão
        if current_user.is_admin:
            query = User.query
        else:
            # Coordenador vê apenas usuários do seu departamento e subdepartamentos
            departamentos_ids = [dept.id for dept in current_user.get_departamentos_acessiveis()]
            query = User.query.filter(User.departamento_id.in_(departamentos_ids))
        
        # Aplicar filtros
        if busca:
            query = query.filter(
                db.or_(
                    User.nome_completo.ilike(f'%{busca}%'),
                    User.username.ilike(f'%{busca}%'),
                    User.email.ilike(f'%{busca}%'),
                    User.cargo.ilike(f'%{busca}%')
                )
            )
        
        if departamento_id:
            query = query.filter(User.departamento_id == departamento_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if ativo:
            query = query.filter(User.ativo == (ativo.lower() == 'true'))
        
        # Ordenação
        usuarios = query.order_by(User.nome_completo.asc()).all()
        
        # Departamentos para filtro
        if current_user.is_admin:
            departamentos = Departamento.query.filter_by(ativo=True).all()
        else:
            departamentos = current_user.get_departamentos_acessiveis()
        
        return render_template(
            'admin/usuarios/usuarios.html',
            usuarios=usuarios,
            departamentos=departamentos,
            filtros={
                'busca': busca,
                'departamento_id': departamento_id,
                'role': role,
                'ativo': ativo
            }
        )
        
    except Exception as e:
        flash(f'Erro ao listar usuários: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.index'))

@usuarios_admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@require_coordenador_ou_admin()
def novo_usuario():
    """Criar novo usuário"""
    if request.method == 'GET':
        try:
            from models.departamento import Departamento
            
            # Departamentos disponíveis baseado na permissão
            if current_user.is_admin:
                departamentos = Departamento.query.filter_by(ativo=True).all()
            else:
                departamentos = current_user.get_departamentos_acessiveis()
            
            return render_template(
                'admin/usuarios/usuario_form.html',
                departamentos=departamentos,
                usuario=None
            )
            
        except Exception as e:
            flash(f'Erro ao carregar formulário: {str(e)}', 'error')
            return redirect(url_for('usuarios_admin.listar_usuarios'))
    
    # POST - Criar usuário
    try:
        from app_mysql_principal import db
        from models.user_departamental import User
        
        # Validar dados obrigatórios
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        nome_completo = request.form.get('nome_completo', '').strip()
        password = request.form.get('password', '').strip()
        
        if not all([username, email, nome_completo, password]):
            flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
            return redirect(url_for('usuarios_admin.novo_usuario'))
        
        # Verificar se username já existe
        if User.query.filter_by(username=username).first():
            flash(f'Nome de usuário "{username}" já existe', 'error')
            return redirect(url_for('usuarios_admin.novo_usuario'))
        
        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            flash(f'Email "{email}" já está em uso', 'error')
            return redirect(url_for('usuarios_admin.novo_usuario'))
        
        # Verificar permissão para criar no departamento
        departamento_id = request.form.get('departamento_id')
        if not current_user.is_admin and not current_user.pode_acessar_departamento(int(departamento_id)):
            flash('Você não tem permissão para criar usuários neste departamento', 'error')
            return redirect(url_for('usuarios_admin.novo_usuario'))
        
        # Criar usuário
        usuario = User(
            username=username,
            email=email,
            nome_completo=nome_completo,
            cpf=request.form.get('cpf', ''),
            telefone=request.form.get('telefone', ''),
            cargo=request.form.get('cargo', ''),
            departamento_id=departamento_id or None,
            role=request.form.get('role', 'OPERADOR'),
            ativo=bool(request.form.get('ativo', True)),
            deve_trocar_senha=bool(request.form.get('deve_trocar_senha', True)),
            criado_por=current_user.id
        )
        
        # Definir senha
        usuario.set_password(password)
        
        # Aplicar permissões baseadas no role
        User.aplicar_permissoes_por_role(usuario, usuario.role)
        
        # Permissões customizadas (apenas admin pode definir)
        if current_user.is_admin:
            usuario.pode_criar_empenhos = bool(request.form.get('pode_criar_empenhos'))
            usuario.pode_editar_empenhos = bool(request.form.get('pode_editar_empenhos'))
            usuario.pode_excluir_empenhos = bool(request.form.get('pode_excluir_empenhos'))
            usuario.pode_criar_contratos = bool(request.form.get('pode_criar_contratos'))
            usuario.pode_editar_contratos = bool(request.form.get('pode_editar_contratos'))
            usuario.pode_excluir_contratos = bool(request.form.get('pode_excluir_contratos'))
            usuario.pode_gerar_relatorios = bool(request.form.get('pode_gerar_relatorios'))
            usuario.pode_acessar_todos_departamentos = bool(request.form.get('pode_acessar_todos_departamentos'))
            usuario.pode_gerenciar_usuarios = bool(request.form.get('pode_gerenciar_usuarios'))
        
        db.session.add(usuario)
        db.session.commit()
        
        flash(f'Usuário "{nome_completo}" criado com sucesso!', 'success')
        return redirect(url_for('usuarios_admin.listar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar usuário: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.novo_usuario'))

@usuarios_admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@require_coordenador_ou_admin()
def editar_usuario(usuario_id):
    """Editar usuário existente"""
    try:
        from app_mysql_principal import db
        from models.user_departamental import User
        from models.departamento import Departamento
        
        usuario = User.query.get_or_404(usuario_id)
        
        # Verificar permissão para editar
        if not current_user.is_admin and not current_user.pode_acessar_departamento(usuario.departamento_id):
            flash('Você não tem permissão para editar este usuário', 'error')
            return redirect(url_for('usuarios_admin.listar_usuarios'))
        
        if request.method == 'GET':
            # Departamentos disponíveis baseado na permissão
            if current_user.is_admin:
                departamentos = Departamento.query.filter_by(ativo=True).all()
            else:
                departamentos = current_user.get_departamentos_acessiveis()
            
            return render_template(
                'admin/usuarios/usuario_form.html',
                departamentos=departamentos,
                usuario=usuario
            )
        
        # POST - Atualizar usuário
        # Validar dados obrigatórios
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        nome_completo = request.form.get('nome_completo', '').strip()
        
        if not all([username, email, nome_completo]):
            flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
            return redirect(url_for('usuarios_admin.editar_usuario', usuario_id=usuario_id))
        
        # Verificar se username já existe (exceto o próprio)
        username_existente = User.query.filter(
            User.username == username,
            User.id != usuario.id
        ).first()
        
        if username_existente:
            flash(f'Nome de usuário "{username}" já existe', 'error')
            return redirect(url_for('usuarios_admin.editar_usuario', usuario_id=usuario_id))
        
        # Verificar se email já existe (exceto o próprio)
        email_existente = User.query.filter(
            User.email == email,
            User.id != usuario.id
        ).first()
        
        if email_existente:
            flash(f'Email "{email}" já está em uso', 'error')
            return redirect(url_for('usuarios_admin.editar_usuario', usuario_id=usuario_id))
        
        # Atualizar dados básicos
        usuario.username = username
        usuario.email = email
        usuario.nome_completo = nome_completo
        usuario.cpf = request.form.get('cpf', '')
        usuario.telefone = request.form.get('telefone', '')
        usuario.cargo = request.form.get('cargo', '')
        usuario.ativo = bool(request.form.get('ativo', True))
        usuario.deve_trocar_senha = bool(request.form.get('deve_trocar_senha'))
        
        # Atualizar departamento (verificar permissão)
        novo_departamento_id = request.form.get('departamento_id')
        if novo_departamento_id != str(usuario.departamento_id):
            if not current_user.is_admin and not current_user.pode_acessar_departamento(int(novo_departamento_id)):
                flash('Você não tem permissão para mover usuário para este departamento', 'error')
                return redirect(url_for('usuarios_admin.editar_usuario', usuario_id=usuario_id))
            usuario.departamento_id = novo_departamento_id or None
        
        # Atualizar role e aplicar permissões
        novo_role = request.form.get('role', usuario.role)
        if novo_role != usuario.role:
            usuario.role = novo_role
            User.aplicar_permissoes_por_role(usuario, novo_role)
        
        # Permissões customizadas (apenas admin pode definir)
        if current_user.is_admin:
            usuario.pode_criar_empenhos = bool(request.form.get('pode_criar_empenhos'))
            usuario.pode_editar_empenhos = bool(request.form.get('pode_editar_empenhos'))
            usuario.pode_excluir_empenhos = bool(request.form.get('pode_excluir_empenhos'))
            usuario.pode_criar_contratos = bool(request.form.get('pode_criar_contratos'))
            usuario.pode_editar_contratos = bool(request.form.get('pode_editar_contratos'))
            usuario.pode_excluir_contratos = bool(request.form.get('pode_excluir_contratos'))
            usuario.pode_gerar_relatorios = bool(request.form.get('pode_gerar_relatorios'))
            usuario.pode_acessar_todos_departamentos = bool(request.form.get('pode_acessar_todos_departamentos'))
            usuario.pode_gerenciar_usuarios = bool(request.form.get('pode_gerenciar_usuarios'))
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('password', '').strip()
        if nova_senha:
            usuario.set_password(nova_senha)
            usuario.deve_trocar_senha = True
        
        db.session.commit()
        
        flash(f'Usuário "{nome_completo}" atualizado com sucesso!', 'success')
        return redirect(url_for('usuarios_admin.listar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao editar usuário: {str(e)}', 'error')
        return redirect(url_for('usuarios_admin.listar_usuarios'))

@usuarios_admin_bp.route('/usuarios/<int:usuario_id>/excluir', methods=['POST'])
@login_required
@require_coordenador_ou_admin()
def excluir_usuario(usuario_id):
    """Excluir usuário (desativar)"""
    try:
        from app_mysql_principal import db
        from models.user_departamental import User
        
        usuario = User.query.get_or_404(usuario_id)
        
        # Verificar permissão para excluir
        if not current_user.is_admin and not current_user.pode_acessar_departamento(usuario.departamento_id):
            return jsonify({
                'success': False,
                'error': 'Você não tem permissão para excluir este usuário'
            }), 403
        
        # Não permitir auto-exclusão
        if usuario.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Você não pode excluir sua própria conta'
            }), 400
        
        # Desativar usuário
        usuario.ativo = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usuário "{usuario.nome_completo}" desativado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir usuário: {str(e)}'
        }), 500

# ============================================================================
# ROTAS AJAX E API
# ============================================================================

@usuarios_admin_bp.route('/api/departamentos')
@login_required
def api_departamentos():
    """API para listar departamentos"""
    try:
        from models.departamento import Departamento
        
        if current_user.is_admin:
            departamentos = Departamento.query.filter_by(ativo=True).all()
        else:
            departamentos = current_user.get_departamentos_acessiveis()
        
        return jsonify({
            'success': True,
            'departamentos': [dept.to_dict() for dept in departamentos]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@usuarios_admin_bp.route('/api/usuarios/<int:usuario_id>')
@login_required
@require_coordenador_ou_admin()
def api_usuario_detalhes(usuario_id):
    """API para obter detalhes de um usuário"""
    try:
        from models.user_departamental import User
        
        usuario = User.query.get_or_404(usuario_id)
        
        # Verificar permissão para visualizar
        if not current_user.is_admin and not current_user.pode_acessar_departamento(usuario.departamento_id):
            return jsonify({
                'success': False,
                'error': 'Acesso negado'
            }), 403
        
        return jsonify({
            'success': True,
            'usuario': usuario.to_dict(incluir_sensiveis=current_user.is_admin)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@usuarios_admin_bp.route('/departamentos/inicializar', methods=['POST'])
@login_required
@require_admin()
def inicializar_departamentos():
    """Inicializar departamentos padrão"""
    try:
        from app_mysql_principal import db
        from models.departamento import Departamento
        
        departamentos_criados = Departamento.criar_departamentos_padrao()
        
        return jsonify({
            'success': True,
            'message': f'{len(departamentos_criados)} departamentos criados com sucesso!',
            'departamentos': [dept.to_dict() for dept in departamentos_criados]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao inicializar departamentos: {str(e)}'
        }), 500
