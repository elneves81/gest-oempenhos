from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
from models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = bool(request.form.get('remember_me'))
        
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.check_password(password):
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Usuário inativo. Contate o administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        # Login com sessão permanente para maior estabilidade
        print(f"DEBUG: Fazendo login do usuário {user.username}")
        
        # Limpar sessão anterior
        from flask import session
        session.clear()
        
        # Fazer login
        login_result = login_user(user, remember=True, duration=None)  
        print(f"DEBUG: Resultado do login_user: {login_result}")
        
        # Configurar sessão manualmente para máxima persistência
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['logged_in'] = True
        
        print(f"DEBUG: Sessão configurada - ID: {session.get('_user_id')}, User ID: {session.get('user_id')}")
        print(f"DEBUG: Sessão permanente: {session.permanent}")
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('painel')
        
        flash(f'Bem-vindo, {user.nome}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login_clean.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout do usuário"""
    from flask import session
    
    if current_user.is_authenticated:
        logout_user()
        flash('Você foi desconectado com sucesso.', 'info')
    else:
        flash('Você já estava desconectado.', 'info')
    
    # Limpar dados de sessão para evitar reautenticação
    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('_user_id', None)
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registro de novos usuários (apenas admins)"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem cadastrar usuários.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        nome = request.form['nome']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = bool(request.form.get('is_admin'))
        
        # Validações
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return redirect(url_for('auth.register'))
        
        # Criar novo usuário
        user = User(
            username=username,
            email=email,
            nome=nome,
            is_admin=is_admin
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuário {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/register.html')

@auth_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    """Lista de usuários (apenas admins) e criação de novos usuários"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Criar novo usuário
        username = request.form.get('username')
        email = request.form.get('email')
        nome = request.form.get('nome')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_admin = 'is_admin' in request.form
        
        # Validações
        if not all([username, email, nome, password, confirm_password]):
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('auth.users'))
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.users'))
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return redirect(url_for('auth.users'))
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return redirect(url_for('auth.users'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já está em uso.', 'error')
            return redirect(url_for('auth.users'))
        
        try:
            # Criar novo usuário
            new_user = User(
                username=username,
                email=email,
                nome=nome,
                is_admin=is_admin
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Usuário {nome} criado com sucesso!', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
            return redirect(url_for('auth.users'))
    
    # GET - listar usuários com filtros
    query = User.query
    
    # Aplicar filtros se fornecidos
    search_filtro = request.args.get('search', '').strip()
    status_filtro = request.args.get('status', '')
    tipo_filtro = request.args.get('tipo', '')
    
    if search_filtro:
        query = query.filter(
            (User.nome.contains(search_filtro)) | 
            (User.username.contains(search_filtro)) | 
            (User.email.contains(search_filtro))
        )
    
    if status_filtro == 'ativo':
        query = query.filter(User.is_active == True)
    elif status_filtro == 'inativo':
        query = query.filter(User.is_active == False)
    
    if tipo_filtro == 'admin':
        query = query.filter(User.is_admin == True)
    elif tipo_filtro == 'user':
        query = query.filter(User.is_admin == False)
    
    users = query.order_by(User.nome).all()
    
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Ativar/desativar usuário via AJAX"""
    if not current_user.is_admin:
        return {'success': False, 'message': 'Acesso negado'}, 403
    
    user = User.query.get_or_404(user_id)
    
    # Não permitir desativar a si mesmo
    if user.id == current_user.id:
        return {'success': False, 'message': 'Você não pode desativar sua própria conta'}, 400
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'ativado' if user.is_active else 'desativado'
        return {
            'success': True, 
            'message': f'Usuário {user.nome} foi {status}.',
            'is_active': user.is_active
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erro: {str(e)}'}, 500

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required  
def delete_user(user_id):
    """Excluir usuário via AJAX"""
    if not current_user.is_admin:
        return {'success': False, 'message': 'Acesso negado'}, 403
    
    user = User.query.get_or_404(user_id)
    
    # Não permitir excluir a si mesmo
    if user.id == current_user.id:
        return {'success': False, 'message': 'Você não pode excluir sua própria conta'}, 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return {'success': True, 'message': f'Usuário {user.nome} foi excluído.'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erro: {str(e)}'}, 500

@auth_bp.route('/users/<int:user_id>/toggle')
@login_required
def toggle_user(user_id):
    """Rota legada mantida para compatibilidade"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'error')
        return redirect(url_for('auth.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'ativado' if user.is_active else 'desativado'
    flash(f'Usuário {user.nome} foi {status}.', 'success')
    
    return redirect(url_for('auth.users'))

@auth_bp.route('/users/<int:user_id>/update', methods=['POST'])
@login_required  
def update_user(user_id):
    """Atualizar dados de um usuário"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem editar usuários.', 'error')
        return redirect(url_for('auth.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Verificar se o username já existe (exceto para o próprio usuário)
    existing_user = User.query.filter(User.username == request.form['username'], User.id != user_id).first()
    if existing_user:
        flash('Nome de usuário já existe. Escolha outro.', 'error')
        return redirect(url_for('auth.users'))
    
    # Verificar se o email já existe (exceto para o próprio usuário)
    existing_email = User.query.filter(User.email == request.form['email'], User.id != user_id).first()
    if existing_email:
        flash('E-mail já existe. Escolha outro.', 'error')
        return redirect(url_for('auth.users'))
    
    # Atualizar dados básicos
    user.nome = request.form['nome']
    user.username = request.form['username'] 
    user.email = request.form['email']
    user.is_admin = 'is_admin' in request.form
    user.is_active = 'is_active' in request.form
    
    # Atualizar senha se fornecida
    if request.form.get('password'):
        if request.form['password'] != request.form.get('confirm_password', ''):
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.users'))
        user.set_password(request.form['password'])
    
    try:
        db.session.commit()
        flash(f'Usuário {user.nome} atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return redirect(url_for('auth.users'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil do usuário"""
    if request.method == 'POST':
        current_user.nome = request.form['nome']
        current_user.email = request.form['email']
        
        # Alterar senha se fornecida
        if request.form.get('new_password'):
            if not current_user.check_password(request.form['current_password']):
                flash('Senha atual incorreta.', 'error')
                return redirect(url_for('auth.profile'))
            
            if request.form['new_password'] != request.form['confirm_password']:
                flash('As novas senhas não coincidem.', 'error')
                return redirect(url_for('auth.profile'))
            
            current_user.set_password(request.form['new_password'])
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')
