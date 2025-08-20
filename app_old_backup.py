from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from datetime import datetime
import os

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configurações para desenvolvimento
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Importações após configuração do app
from models import db, User

# Inicializar extensões  
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Página inicial"""
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sistema de Login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('painel'))
        else:
            flash('Usuário ou senha incorretos', 'error')
            return redirect(url_for('login'))
    
    # Renderizar template de login original
    try:
        return render_template('auth/login_clean.html')
    except:
        # Fallback se template não existir
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Sistema de Empenhos - Login</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 400px; width: 100%; }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        .btn { width: 100%; background: #667eea; color: white; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Sistema de Empenhos Municipal</h2>
        <form method="post">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit" class="btn">Entrar</button>
        </form>
    </div>
</body>
</html>'''

@app.route('/painel')
@login_required
def painel():
    """Dashboard principal do sistema"""
    try:
        return render_template('dashboard.html', titulo='Dashboard')
    except:
        # Fallback dashboard simples
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Sistema de Empenhos</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/painel">Sistema de Empenhos</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/logout">Sair</a>
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        <h1>Dashboard</h1>
        <p>Bem-vindo, {current_user.nome if hasattr(current_user, 'nome') else current_user.username}!</p>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Empenhos</h5>
                        <p class="card-text">Gerenciar empenhos</p>
                        <a href="/empenhos/" class="btn btn-primary">Acessar</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Contratos</h5>
                        <p class="card-text">Gerenciar contratos</p>
                        <a href="/contratos/" class="btn btn-primary">Acessar</a>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Relatórios</h5>
                        <p class="card-text">Visualizar relatórios</p>
                        <a href="/relatorios/" class="btn btn-primary">Acessar</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/favicon.ico')
def favicon():
    return '', 204

# Registrar blueprints apenas os que existem
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

try:
    from routes.relatorios import relatorios_bp
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    print("✅ Blueprint relatorios registrado")
except ImportError as e:
    print(f"Blueprint relatorios não encontrado: {e}")

# Função para criar tabelas
def create_tables():
    with app.app_context():
        db.create_all()
        print("✅ Tabelas criadas/verificadas")

# Error handlers simples
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
<head><title>Erro interno</title></head>
<body>
    <h1>Erro interno do servidor</h1>
    <p>Ocorreu um erro interno. Tente novamente.</p>
    <a href="/">Voltar</a>
</body>
</html>''', 500

if __name__ == '__main__':
    from waitress import serve
    
    create_tables()
    
    print("\n🏛️  SISTEMA DE EMPENHOS MUNICIPAL")
    print("==================================================")
    print("🔧 Versão: Sistema Original Limpo")
    print("🏛️  Desenvolvido para: Gestão Municipal")
    print("==================================================")
    
    print("\n📊 CONFIGURAÇÕES DO SERVIDOR")
    print("------------------------------")
    print("🌐 Host: 0.0.0.0")
    print("🔌 Porta: 8001")
    print("🧵 Threads: 6")
    print("🔗 Conexões máx: 100")
    print("------------------------------")
    
    print("📍 ENDEREÇOS DE ACESSO")
    print("   • Local: http://127.0.0.1:8001")
    print("   • Rede: http://10.0.50.79:8001")
    print("------------------------------")
    
    print("🎯 FUNCIONALIDADES DISPONÍVEIS")
    print("   ✅ Login com template original ou fallback")
    print("   ✅ Dashboard funcional")
    print("   ✅ Blueprints registrados dinamicamente")
    print("   ✅ Error handlers simples")
    print("   ✅ Waitress para produção")
    print("------------------------------")
    
    print("💡 Para parar: Ctrl+C")
    print("🔍 Servidor iniciando...")
    print("==================================================")
    
    serve(app, host='0.0.0.0', port=8001, threads=6, connection_limit=100)
