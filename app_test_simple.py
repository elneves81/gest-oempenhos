from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, date, timedelta
import os

# =========================
# Configuração da aplicação
# =========================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'empenhos-municipal-guarapuava-2025-sistema-robusto-sessao-permanente-admin123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("🚀 Iniciando aplicação Flask...")

# SQLite com threads
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"check_same_thread": False}
}

# Configurações de sessão
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_PERMANENT'] = True
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=1)

print("✅ Configurações básicas definidas")

# Importação dos modelos
try:
    from models import db, User, Empenho, Contrato
    print("✅ Models importados com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar models: {e}")
    raise

# Inicialização das extensões
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.session_protection = 'basic'
login_manager.remember_cookie_duration = timedelta(days=1)

print("✅ Extensões inicializadas")

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None

# Importação dos blueprints
print("📦 Importando blueprints...")

try:
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    print("✅ auth_bp registrado")
except Exception as e:
    print(f"❌ Erro no auth_bp: {e}")

try:
    from routes.empenhos import empenhos_bp
    app.register_blueprint(empenhos_bp, url_prefix='/empenhos')
    print("✅ empenhos_bp registrado")
except Exception as e:
    print(f"❌ Erro no empenhos_bp: {e}")

try:
    from routes.contratos import contratos_bp
    app.register_blueprint(contratos_bp, url_prefix='/contratos')
    print("✅ contratos_bp registrado")
except Exception as e:
    print(f"❌ Erro no contratos_bp: {e}")

try:
    from routes.relatorios import relatorios_bp
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    print("✅ relatorios_bp registrado")
except Exception as e:
    print(f"❌ Erro no relatorios_bp: {e}")

try:
    from routes.notas import notas_bp
    app.register_blueprint(notas_bp, url_prefix='/notas')
    print("✅ notas_bp registrado")
except Exception as e:
    print(f"❌ Erro no notas_bp: {e}")

try:
    from routes.workflow import workflow_bp
    app.register_blueprint(workflow_bp, url_prefix='/workflow')
    print("✅ workflow_bp registrado")
except Exception as e:
    print(f"❌ Erro no workflow_bp: {e}")

# Rotas básicas
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    return redirect(url_for('auth.login'))

@app.route('/painel')
@login_required
def painel():
    try:
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        
        context = {
            'total_empenhos': total_empenhos,
            'total_contratos': total_contratos,
            'valor_total_contratos': 0,
            'contratos_criticos': [],
            'now': datetime.now
        }
        
        return render_template('painel.html', **context)
    except Exception as e:
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>Dashboard - Sistema de Empenhos</h1>
        <div class="alert alert-info">
            <p>Dashboard funcionando!</p>
            <p><strong>Usuário:</strong> {current_user.nome if current_user.is_authenticated else 'Não logado'}</p>
            <p><strong>Erro:</strong> {str(e)}</p>
        </div>
        <div class="row">
            <div class="col-md-3">
                <a href="/empenhos/" class="btn btn-primary w-100 mb-2">Empenhos</a>
            </div>
            <div class="col-md-3">
                <a href="/contratos/" class="btn btn-info w-100 mb-2">Contratos</a>
            </div>
            <div class="col-md-3">
                <a href="/relatorios/" class="btn btn-success w-100 mb-2">Relatórios</a>
            </div>
            <div class="col-md-3">
                <a href="/auth/logout" class="btn btn-secondary w-100 mb-2">Logout</a>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/simple')
def simple_test():
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Teste Simples</title>
</head>
<body>
    <h1>✅ Servidor Flask Funcionando!</h1>
    <p>Sistema de Empenhos - Guarapuava</p>
    <p>Hora atual: ''' + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + '''</p>
    <p><a href="/">Ir para o Dashboard</a></p>
</body>
</html>'''

def create_tables():
    """Criar tabelas do banco de dados"""
    with app.app_context():
        print("🗄️ Criando tabelas do banco de dados...")
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@sistema.com',
                nome='Administrador',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado - Login: admin, Senha: admin123")
        else:
            print("✅ Usuário admin já existe")

if __name__ == '__main__':
    print("🔧 Criando tabelas...")
    create_tables()
    print("🌐 Iniciando servidor Flask...")
    print("📍 Acesse: http://localhost:5000")
    print("🔑 Login: admin | Senha: admin123")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
