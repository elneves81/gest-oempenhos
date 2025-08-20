from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user, login_user
from datetime import datetime
import os

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = 'empenhos-municipal-guarapuava-2025-sistema-robusto-sessao-permanente-admin123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configurações de sessão para melhor persistência
app.config['SESSION_COOKIE_SECURE'] = False  # HTTP em desenvolvimento
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas
app.config['SESSION_COOKIE_NAME'] = 'empenhos_session'
app.config['SESSION_PERMANENT'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 24 horas para remember me
app.config['SESSION_COOKIE_MAX_SIZE'] = 4093  # Tamanho máximo do cookie
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Renovar sessão a cada request

# Configurações para desenvolvimento - desabilitar cache
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

# Garantir Content-Type correto para HTML
@app.after_request
def after_request(response):
    if response.mimetype.startswith('text/html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        # Header para forçar Standards Mode
        response.headers['X-UA-Compatible'] = 'IE=edge'
    return response

# Importações após configuração do app
from models import db, User, Empenho, Contrato

# Inicializar extensões
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.session_protection = "basic"  # Proteção básica de sessão

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# DEBUG: Middleware de debug DESABILITADO para evitar deadlocks
# @app.before_request
# def debug_request():
#     print(f"DEBUG REQUEST: {request.method} {request.path}")

@app.route('/')
def index():
    """Página inicial - redireciona para login se não autenticado"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sistema de Login Simplificado"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Buscar usuário no banco
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)  # Remember ativado
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos', 'error')
    
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Sistema Municipal de Empenhos - Login</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 50px; text-align: center; }
        .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0056b3; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Sistema Municipal de Empenhos</h2>
        <h3>Login</h3>
        <form method="post">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit" class="btn">Entrar</button>
        </form>
        <p><small>Sistema Robusto - Versão de Produção</small></p>
    </div>
</body>
</html>'''

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard Principal"""
    return redirect(url_for('painel'))

@app.route('/painel')
@login_required  
def painel():
    """Painel Principal Executivo"""
    try:
        from sqlalchemy import func
        from datetime import datetime, date, timedelta
        
        # Estatísticas básicas
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        contratos_ativos = Contrato.query.filter(Contrato.status.in_(['Ativo', 'ATIVO'])).count()
        
        # Novos empenhos este mês
        inicio_mes = datetime.now().replace(day=1)
        novos_empenhos_mes = Empenho.query.filter(Empenho.data_criacao >= inicio_mes).count()
        
        # Valor total dos empenhos
        valor_total_empenhos = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
        
        # Valor total dos contratos ativos
        valor_total_contratos = db.session.query(func.sum(Contrato.valor_total)).filter(
            Contrato.status.in_(['Ativo', 'ATIVO'])
        ).scalar() or 0
        
        # Data atual para cálculo de dias restantes
        hoje = datetime.now().date()
        
        # Contratos vencendo em 30 dias
        data_limite = hoje + timedelta(days=30)
        vencendo_30 = Contrato.query.filter(
            Contrato.status.in_(['Ativo', 'ATIVO']),
            Contrato.data_fim <= data_limite,
            Contrato.data_fim >= hoje
        ).count()
        
        # Buscar top 5 contratos por valor
        top_contratos = Contrato.query.filter(
            Contrato.status.in_(['Ativo', 'ATIVO'])
        ).order_by(Contrato.valor_total.desc()).limit(5).all()
        
        # Empenhos recentes (últimos 5)
        empenhos_recentes = Empenho.query.order_by(Empenho.data_criacao.desc()).limit(5).all()
        
        return render_template('dashboard.html',
            total_empenhos=total_empenhos,
            total_contratos=total_contratos,
            contratos_ativos=contratos_ativos,
            novos_empenhos_mes=novos_empenhos_mes,
            valor_total_empenhos=valor_total_empenhos,
            valor_total_contratos=valor_total_contratos,
            vencendo_30=vencendo_30,
            top_contratos=top_contratos,
            empenhos_recentes=empenhos_recentes
        )
        
    except Exception as e:
        print(f"Erro no painel: {e}")
        # Fallback simples em caso de erro
        return '''<!DOCTYPE html>
<html><head><title>Dashboard</title></head>
<body><h1>Dashboard Funcionando!</h1>
<p>Sistema funcionando em modo simplificado.</p>
<a href="/relatorios/">Ir para Relatórios</a>
</body></html>'''

@app.route('/test')
def test():
    """Rota de teste básico"""
    return 'Sistema funcionando!'

@app.route('/favicon.ico')
def favicon():
    """Favicon básico para evitar erros 404"""
    return '', 204

@app.route('/logout')
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Registrar blueprints
from routes.relatorios import relatorios_bp
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

# Registrar outros blueprints existentes
try:
    from routes.empenhos import empenhos_bp
    app.register_blueprint(empenhos_bp, url_prefix='/empenhos')
    print("✅ Blueprint empenhos registrado")
except ImportError as e:
    print(f"Blueprint empenhos não encontrado: {e}")

try:
    from routes.contratos import contratos_bp
    app.register_blueprint(contratos_bp, url_prefix='/contratos')
    print("✅ Blueprint contratos registrado")
except ImportError as e:
    print(f"Blueprint contratos não encontrado: {e}")

# Blueprints opcionais
try:
    from routes.usuarios import usuarios_bp
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    print("✅ Blueprint usuarios registrado")
except ImportError:
    print("Blueprint usuarios não encontrado")

try:
    from routes.anexos import anexos_bp
    app.register_blueprint(anexos_bp, url_prefix='/anexos')
    print("✅ Blueprint anexos registrado")
except ImportError:
    print("Blueprint anexos não encontrado")

try:
    from routes.anotacoes import anotacoes_bp
    app.register_blueprint(anotacoes_bp, url_prefix='/anotacoes')
    print("✅ Blueprint anotacoes registrado")
except ImportError:
    print("Blueprint anotacoes não encontrado")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return '''<!DOCTYPE html>
<html>
<head><title>Página não encontrada</title></head>
<body>
    <h1>Página não encontrada</h1>
    <p>A página solicitada não foi encontrada.</p>
    <a href="/">Voltar ao início</a>
</body>
</html>''', 404

@app.errorhandler(500)
def internal_error(error):
    return '''<!DOCTYPE html>
<html>
<head><title>Erro 500</title></head>
<body>
    <h1>Erro Interno do Servidor</h1>
    <p>Ocorreu um erro interno. Tente novamente.</p>
    <a href="/">Voltar</a>
</body>
</html>''', 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
