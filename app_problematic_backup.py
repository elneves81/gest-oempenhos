from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
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
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Página inicial"""
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    return redirect(url_for('auth.login'))

@app.route('/painel')
@login_required
def painel():
    """Dashboard principal do sistema"""
    return render_template('dashboard.html', titulo='Dashboard')

# Registrar blueprints
from routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from routes.empenhos import empenhos_bp
app.register_blueprint(empenhos_bp, url_prefix='/empenhos')

from routes.contratos import contratos_bp
app.register_blueprint(contratos_bp, url_prefix='/contratos')

from routes.relatorios import relatorios_bp
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

# Registrar blueprints opcionais
try:
    from routes.usuarios import usuarios_bp
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
except ImportError:
    pass

try:
    from routes.anexos import anexos_bp
    app.register_blueprint(anexos_bp, url_prefix='/anexos')
except ImportError:
    pass

try:
    from routes.anotacoes import anotacoes_bp
    app.register_blueprint(anotacoes_bp, url_prefix='/anotacoes')
except ImportError:
    pass

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    from waitress import serve
    
    with app.app_context():
        db.create_all()
        print("✅ Tabelas do banco criadas/verificadas")
    
    print("\n🏛️  SISTEMA DE EMPENHOS MUNICIPAL")
    print("==================================================")
    print("🔧 Versão: Sistema Original com Waitress")
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
    print("   ✅ Sistema de Login com templates originais")
    print("   ✅ Dashboard principal")
    print("   ✅ Gestão de empenhos")
    print("   ✅ Gestão de contratos") 
    print("   ✅ Sistema de relatórios")
    print("   ✅ Autenticação segura")
    print("------------------------------")
    
    print("💡 Para parar: Ctrl+C")
    print("🔍 Servidor iniciando...")
    print("==================================================")
    
    serve(app, host='0.0.0.0', port=8001, threads=6, connection_limit=100)
