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
app.config['UPLOAD_FOLDER'] = 'uploads'

# SQLite com threads (debug server)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"check_same_thread": False}
}

# Criar diretório de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Importação dos modelos
from models import db, User, Empenho, Contrato, AditivoContratual

# Inicialização das extensões
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'basic'
login_manager.remember_cookie_duration = timedelta(days=1)

@login_manager.user_loader
def load_user(user_id):
    try:
        user = User.query.get(int(user_id))
        return user
    except (TypeError, ValueError) as e:
        return None

# Importação das rotas modulares / blueprints
print("Importando blueprints...")
from routes.auth import auth_bp
from routes.workflow import workflow_bp

# Registro dos blueprints
print("Registrando blueprints...")
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(workflow_bp, url_prefix='/workflow')

# Rota simples
@app.route('/')
def index():
    """Página inicial - redireciona para login se não autenticado"""
    if current_user.is_authenticated:
        return "<h1>Sistema funcionando! Usuário logado</h1>"
    return redirect(url_for('auth.login'))

@app.route('/favicon.ico')
def favicon():
    return '', 204

def create_tables():
    """Criar tabelas do banco de dados"""
    with app.app_context():
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
            print("Usuário admin criado - Login: admin, Senha: admin123")

# ============
# Entrypoint
# ============
if __name__ == '__main__':
    from waitress import serve
    
    print("Criando tabelas...")
    create_tables()
    
    print("\n🏛️  SISTEMA DE EMPENHOS MUNICIPAL")
    print("🔌 Porta: 8001")
    print("🔍 Servidor iniciando...")
    
    serve(app, host='0.0.0.0', port=8001, threads=6, connection_limit=100)
