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
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = bool(request.form.get('remember_me'))
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Usuário inativo. Contate o administrador.', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember_me)
        user.update_last_login()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        
        flash(f'Bem-vindo, {user.nome}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
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

@auth_bp.route('/users')
@login_required
def users():
    """Lista de usuários (apenas admins)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/<int:user_id>/toggle')
@login_required
def toggle_user(user_id):
    """Ativar/desativar usuário"""
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
