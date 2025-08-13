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

# Configurações para desenvolvimento - desabilitar cache
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Importação das rotas modulares
from routes.auth import auth_bp
from routes.empenhos import empenhos_bp
from routes.contratos import contratos_bp
from routes.relatorios import relatorios_bp

# Registro dos blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(empenhos_bp, url_prefix='/empenhos')
app.register_blueprint(contratos_bp, url_prefix='/contratos')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

@app.route('/')
@login_required
def index():
    """Página inicial - Dashboard"""
    # Estatísticas de empenhos
    total_empenhos = Empenho.query.count()
    valor_total_empenhos = db.session.query(db.func.sum(Empenho.valor_empenhado)).scalar() or 0
    empenhos_recentes = Empenho.query.order_by(Empenho.data_criacao.desc()).limit(5).all()
    
    # Estatísticas de contratos
    total_contratos = Contrato.query.count()
    contratos_ativos = Contrato.query.filter_by(status='ATIVO').count()
    valor_total_contratos = db.session.query(db.func.sum(Contrato.valor_total)).scalar() or 0
    
    # Contratos vencendo em 30 dias (compatível com SQLite)
    from datetime import timedelta
    data_limite = datetime.now().date() + timedelta(days=30)
    contratos_vencendo = Contrato.query.filter(
        Contrato.data_fim <= data_limite,
        Contrato.status == 'ATIVO'
    ).count()
    
    return render_template('dashboard.html', 
                         total_empenhos=total_empenhos,
                         valor_total_empenhos=valor_total_empenhos,
                         empenhos_recentes=empenhos_recentes,
                         total_contratos=total_contratos,
                         contratos_ativos=contratos_ativos,
                         valor_total_contratos=valor_total_contratos,
                         contratos_vencendo=contratos_vencendo)

@app.context_processor
def utility_processor():
    """Funções utilitárias disponíveis nos templates"""
    def format_currency(value):
        if value is None:
            return "R$ 0,00"
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def format_date(date):
        if date is None:
            return ""
        return date.strftime('%d/%m/%Y')
    
    return dict(format_currency=format_currency, format_date=format_date)

# Registrar filtros Jinja2
@app.template_filter('format_currency')
def format_currency_filter(value):
    """Filtro para formatar valores monetários"""
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

@app.template_filter('format_date')
def format_date_filter(date):
    """Filtro para formatar datas"""
    if date is None:
        return ""
    return date.strftime('%d/%m/%Y')

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

# Rota de teste para JavaScript
@app.route('/teste-js')
@login_required
def teste_js():
    return render_template('teste_js.html')

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
