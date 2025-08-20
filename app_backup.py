from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user, login_user
from datetime import datetime
import os

# Configuração da aplicação
app @app.route('/painel')
@login_required  
def painel():
    """Painel Principal Executivo - MODO SIMPLIFICADO"""
    return '''<!DOCTYPE html>
<html><head><title>Dashboard</title></head>
<body><h1>Dashboard Funcionando!</h1>
<p>Sistema funcionando em modo simplificado.</p>
<a href="/relatorios/">Ir para Relatórios</a>
</body></html>'''

@app.route('/test')__)
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

# Handlers de erro customizados para garantir DOCTYPE correto
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404_simple.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# Middleware para debug de requisições - DESABILITADO TEMPORARIAMENTE
@app.before_request
def before_request():
    # print(f"DEBUG: Requisição para {request.path}")
    
    # Debug de sessão
    # from flask import session
    # from flask_login import current_user
    
    if request.path.startswith('/static/'):
        return  # Skip static files
        
    # print(f"DEBUG: current_user.is_authenticated: {current_user.is_authenticated}")
    # print(f"DEBUG: Session user_id: {session.get('user_id')}")
    # print(f"DEBUG: Session _user_id: {session.get('_user_id')}")
    # print(f"DEBUG: Session logged_in: {session.get('logged_in')}")
    
    # COMENTADO TEMPORARIAMENTE PARA EVITAR DEADLOCK
    # Se temos dados de sessão mas o Flask-Login não reconhece, tentar reautenticar
    # if not current_user.is_authenticated and session.get('logged_in') and session.get('user_id'):
    #     try:
    #         from models import User
    #         user = User.query.get(session.get('user_id'))
    #         if user:
    #             login_user(user, remember=True)
    #             print(f"DEBUG: Usuário reautenticado: {user.username}")
    #     except Exception as e:
    #         print(f"DEBUG: Erro na reautenticação: {e}")

@app.errorhandler(500)
def internal_error(error):
    print(f"ERRO 500: {error}")
    return render_template('errors/500.html'), 500

# Criar diretório de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Importação dos modelos
from models import db, User, Empenho, Contrato, AditivoContratual

# Tentar importar NotaFiscal se existir
try:
    from models import NotaFiscal
    NOTAS_DISPONIVEL = True
except ImportError:
    NOTAS_DISPONIVEL = False

# Inicialização das extensões
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'basic'  # Proteção básica para evitar logout automático
login_manager.remember_cookie_duration = 86400  # 24 horas

@login_manager.user_loader
def load_user(user_id):
    try:
        print(f"DEBUG LOAD_USER: Tentando carregar usuário ID: {user_id}")
        user = User.query.get(int(user_id))
        if user:
            print(f"DEBUG LOAD_USER: Usuário carregado: {user.username}")
        else:
            print(f"DEBUG LOAD_USER: Usuário não encontrado para ID: {user_id}")
        return user
    except (TypeError, ValueError) as e:
        print(f"DEBUG LOAD_USER: Erro ao carregar usuário: {e}")
        return None

# Importação das rotas modulares
from routes.auth import auth_bp
from routes.workflow import workflow_bp

# Tentar importar blueprints das rotas existentes primeiro
try:
    from routes.empenhos import empenhos_bp
    from routes.contratos import contratos_bp
    from routes.relatorios import relatorios_bp
    from routes.notas import notas_bp
    print("✅ Usando blueprints das rotas existentes")
except ImportError as e:
    print(f"⚠️ Erro ao importar rotas existentes: {e}")
    # Fallback para novos blueprints
    try:
        from blueprints_new.blueprints.empenhos import bp as empenhos_bp
        from blueprints_new.blueprints.contratos import bp as contratos_bp
        from blueprints_new.blueprints.relatorios import bp as relatorios_bp
        from blueprints_new.blueprints.notas import bp as notas_bp
        print("✅ Usando novos blueprints da pasta blueprints_new")
    except ImportError as e2:
        print(f"❌ Erro ao importar novos blueprints: {e2}")
        # Criar blueprints vazios como fallback
        from flask import Blueprint
        empenhos_bp = Blueprint('empenhos', __name__, url_prefix='/empenhos')
        contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')
        relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')
        notas_bp = Blueprint('notas', __name__, url_prefix='/notas')
        print("⚠️ Usando blueprints vazios como fallback")

# Registro dos blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

# Rota de teste para diagnosticar problemas de sessão
@app.route('/test-session')
def test_session():
    from flask_login import current_user
    from flask import session
    return f"""
    <h1>Teste de Sessão</h1>
    <p>Usuário autenticado: {current_user.is_authenticated}</p>
    <p>ID do usuário: {getattr(current_user, 'id', 'None')}</p>
    <p>Nome do usuário: {getattr(current_user, 'username', 'None')}</p>
    <p>Session ID: {session.get('_user_id', 'None')}</p>
    <p>Session Permanent: {session.permanent}</p>
    <p>Session: {dict(session)}</p>
    <a href="/auth/login">Login</a> | <a href="/">Home</a>
    """
app.register_blueprint(empenhos_bp, url_prefix='/empenhos')
app.register_blueprint(contratos_bp, url_prefix='/contratos')
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
app.register_blueprint(notas_bp, url_prefix='/notas')
app.register_blueprint(workflow_bp, url_prefix='/workflow')

# Importar e registrar o blueprint do chat
try:
    from routes.chat import chat
    app.register_blueprint(chat)
    print("✅ Chat blueprint registrado com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao registrar chat blueprint: {e}")
    print("⚠️ Chat funcionará em modo básico")

# Importar e registrar o chat offline
try:
    from routes.chat_offline import chat_offline
    app.register_blueprint(chat_offline)
    print("✅ Chat offline registrado com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao registrar chat offline: {e}")

# Rota de debug temporária
try:
    from debug_relatorios_route import debug_bp
    app.register_blueprint(debug_bp)
    print("✅ Debug relatorios registrado!")
except Exception as e:
    print(f"⚠️ Erro ao registrar debug relatorios: {e}")

# Rota para favicon
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/')
def index():
    """Página inicial - redireciona para login se não autenticado"""
    if current_user.is_authenticated:
        return redirect(url_for('painel'))
    return redirect(url_for('auth.login'))

@app.route('/login')
def login_redirect():
    """Rota de conveniência que redireciona para auth.login"""
    return redirect(url_for('auth.login'))

@app.route('/empenhos')
def empenhos_redirect():
    """Rota de conveniência que redireciona para empenhos.index"""
    return redirect(url_for('empenhos.index'))

@app.route('/contratos')
def contratos_redirect():
    """Rota de conveniência que redireciona para contratos.index"""
    return redirect(url_for('contratos.index'))

@app.route('/painel')
@login_required  
def painel():
    """Painel Principal Executivo - MODO SIMPLIFICADO"""
    return '''<!DOCTYPE html>
<html><head><title>Dashboard</title></head>
<body><h1>Dashboard Funcionando!</h1>
<p>Sistema funcionando em modo simplificado.</p>
<a href="/relatorios/">Ir para Relatórios</a>
</body></html>'''
        
        # Estatísticas básicas
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        contratos_ativos = Contrato.query.filter(Contrato.status.in_(['Ativo', 'ATIVO'])).count()
        
        # Novos empenhos este mês
        inicio_mes = datetime.now().replace(day=1)
        novos_empenhos_mes = Empenho.query.filter(Empenho.data_criacao >= inicio_mes).count()
        
        # Valor total dos contratos ativos
        valor_total = db.session.query(func.sum(Contrato.valor_total)).filter(Contrato.status.in_(['Ativo', 'ATIVO'])).scalar() or 0
        
        # Data atual para cálculo de dias restantes
        hoje = datetime.now().date()
        
        # Buscar todos os contratos ativos com datas de término
        contratos = Contrato.query.filter(
            Contrato.status.in_(['Ativo', 'ATIVO']),
            Contrato.data_fim.isnot(None)
        ).all()
        
        # Buscar empenhos para estatísticas
        empenhos = Empenho.query.order_by(Empenho.data_criacao.desc()).all()
        
        # Calcular dias restantes e categorizar contratos
        contratos_com_dias = []
        for contrato in contratos:
            if contrato.data_fim:
                dias_restantes = (contrato.data_fim - hoje).days
                contrato.dias_restantes = dias_restantes
                contratos_com_dias.append(contrato)
        
        # Categorizar por tempo restante
        contratos_criticos = [c for c in contratos_com_dias if c.dias_restantes <= 30]
        contratos_atencao = [c for c in contratos_com_dias if 31 <= c.dias_restantes <= 60]
        contratos_ok = [c for c in contratos_com_dias if c.dias_restantes > 60]
        
        # Ordenar por dias restantes (mais críticos primeiro)
        contratos_criticos.sort(key=lambda x: x.dias_restantes)
        contratos_atencao.sort(key=lambda x: x.dias_restantes)
        contratos_ok.sort(key=lambda x: x.dias_restantes)
        
        print("DEBUG DASHBOARD: Preparando contexto para template")
        
        # Preparar contexto para o template
        context = {
            'total_empenhos': total_empenhos,
            'total_contratos': total_contratos,
            'contratos_ativos': contratos_ativos,
            'novos_empenhos_mes': novos_empenhos_mes,
            'valor_total_contratos': valor_total,
            'valor_total_empenhos': sum(e.valor_empenhado for e in empenhos if e.valor_empenhado),
            'contratos_criticos': contratos_criticos,
            'contratos_atencao': contratos_atencao,
            'contratos_normais': contratos_ok,
            'contratos_criticos_count': len(contratos_criticos),
            'empenhos_pendentes': len([e for e in empenhos if e.status == 'PENDENTE']),
            'empenhos_aprovados': len([e for e in empenhos if e.status == 'APROVADO']),
            'empenhos_pagos': len([e for e in empenhos if e.status == 'PAGO']),
            'empenhos_rejeitados': len([e for e in empenhos if e.status == 'REJEITADO']),
            'ultimos_empenhos': empenhos[:10],
            'now': datetime.now
        }
        
        print(f"DEBUG DASHBOARD: Renderizando dashboard_clean.html com contexto: {len(context)} variáveis")
        
        # Renderização direta do dashboard executivo
        print(f"DEBUG DASHBOARD: Renderizando dashboard_clean.html com contexto: {len(context)} variáveis")
        
        # Formatar valores monetários
        context['valor_total_formatted'] = f"{valor_total:,.0f}".replace(',', '.')
        
        return render_template('painel.html', **context)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERRO NO DASHBOARD: {e}")
        print(error_details)
        
        # Fallback para dashboard simples em caso de erro
        try:
            context = {
                'total_empenhos': Empenho.query.count() if 'Empenho' in globals() else 0,
                'total_contratos': Contrato.query.count() if 'Contrato' in globals() else 0,
                'contratos_criticos': [],
                'contratos_atencao': [],
                'contratos_ok': [],
                'valor_total_contratos': 0,
                'contratos_criticos_count': 0,
                'now': datetime.now
            }
            return render_template('dashboard_simple.html', **context)
        except:
            # Último recurso - HTML estático
            return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Erro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="alert alert-danger">
            <h4>Erro no Dashboard</h4>
            <p><strong>Erro:</strong> {str(e)}</p>
            <p><strong>Usuário:</strong> {current_user.nome if current_user.is_authenticated else 'Não logado'}</p>
            <details>
                <summary>Detalhes técnicos</summary>
                <pre>{error_details}</pre>
            </details>
        </div>
        
        <div class="row">
            <div class="col-md-4">
                <a href="/empenhos/" class="btn btn-primary w-100 mb-2">Empenhos</a>
            </div>
            <div class="col-md-4">
                <a href="/contratos/" class="btn btn-info w-100 mb-2">Contratos</a>
            </div>
            <div class="col-md-4">
                <a href="/auth/logout" class="btn btn-secondary w-100 mb-2">Logout</a>
            </div>
        </div>
    </div>
</body>
</html>'''


@app.route('/test')
def test_doctype():
    """Página de teste para DOCTYPE"""
    from datetime import datetime
    return render_template('test.html', now=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))


@app.route('/simple')
def simple_test():
    """Teste simples sem template"""
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste Simples</title>
</head>
<body>
    <h1>Servidor Funcionando!</h1>
    <p>Teste simples do servidor</p>
    <script>
        console.log('Modo do documento:', document.compatMode);
        if (document.compatMode === 'CSS1Compat') {
            console.log('✅ Standards Mode ativo');
        } else {
            console.log('❌ Quirks Mode detectado');
        }
    </script>
</body>
</html>'''


@app.route('/debug')
def debug_templates():
    """Debug dos templates"""
    try:
        return render_template('test.html', now='Teste de Template')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro Template</title>
</head>
<body>
    <h1>Erro no Template</h1>
    <p>Erro: {str(e)}</p>
</body>
</html>'''


@app.route('/debug-login')
def debug_login():
    """Debug do login e dashboard"""
    from flask_login import login_user
    from models import User
    
    try:
        # Fazer login automaticamente
        user = User.query.filter_by(username='admin').first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            return 'Usuário admin não encontrado'
    except Exception as e:
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro Login Debug</title>
</head>
<body>
    <h1>Erro no Login Debug</h1>
    <p>Erro: {str(e)}</p>
</body>
</html>'''


@app.route('/debug-dashboard')
@login_required 
def debug_dashboard():
    """Debug específico do dashboard"""
    try:
        from datetime import datetime, date, timedelta
        
        # Testar consultas básicas
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        
        # Dados básicos para o dashboard
        context = {
            'total_empenhos': total_empenhos,
            'total_contratos': total_contratos,
            'contratos_criticos': [],
            'contratos_atencao': [],
            'contratos_ok': [],
            'valor_total_contratos': 0,
            'format_currency': format_currency_filter
        }
        
        return render_template('dashboard.html', **context)
        
    except Exception as e:
        import traceback
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro Dashboard</title>
</head>
<body>
    <h1>Erro no Dashboard</h1>
    <p><strong>Erro:</strong> {str(e)}</p>
    <pre>{traceback.format_exc()}</pre>
</body>
</html>'''


@app.route('/dashboard-simple')
def dashboard_simple():
    """Dashboard simples para teste"""
    try:
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        
        return render_template('dashboard_simple.html', 
                             total_empenhos=total_empenhos,
                             total_contratos=total_contratos)
    except Exception as e:
        import traceback
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro Dashboard Simples</title>
</head>
<body>
    <h1>Erro no Dashboard Simples</h1>
    <p><strong>Erro:</strong> {str(e)}</p>
    <pre>{traceback.format_exc()}</pre>
</body>
</html>'''


@app.route('/dashboard-executivo')
@login_required
def dashboard_executivo():
    """Dashboard Executivo Completo com Análise de Contratos"""
    try:
        from datetime import datetime, timedelta
        
        # Estatísticas básicas
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        contratos_ativos = Contrato.query.filter_by(status='ATIVO').count()
        
        # Cálculo do valor total (sum of valor_total)
        valor_total = db.session.query(db.func.sum(Contrato.valor_total)).scalar() or 0
        
        # Data atual para cálculos
        hoje = datetime.now().date()
        
        # Buscar todos os contratos ativos com datas de fim
        contratos = Contrato.query.filter(
            Contrato.status == 'ATIVO',
            Contrato.data_fim.isnot(None)
        ).all()
        
        # Classificar contratos por urgência
        contratos_criticos = []
        contratos_atencao = []
        contratos_ok = []
        
        for contrato in contratos:
            if contrato.data_fim:
                dias_restantes = (contrato.data_fim - hoje).days
                contrato.dias_restantes = dias_restantes  # Adiciona propriedade temporária
                
                if dias_restantes <= 30:
                    contratos_criticos.append(contrato)
                elif dias_restantes <= 60:
                    contratos_atencao.append(contrato)
                else:
                    contratos_ok.append(contrato)
        
        # Ordenar contratos críticos por urgência (menor número de dias primeiro)
        contratos_criticos.sort(key=lambda x: x.dias_restantes)
        
        # Preparar contexto para o template
        context = {
            'total_empenhos': total_empenhos,
            'total_contratos': total_contratos,
            'contratos_ativos': contratos_ativos,
            'valor_total': valor_total,
            'contratos_criticos': contratos_criticos,
            'contratos_atencao': contratos_atencao,
            'contratos_ok': contratos_ok,
            'hoje': hoje
        }
        
        return render_template('dashboard_executivo_novo.html', **context)
        
    except Exception as e:
        import traceback
        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro Dashboard Executivo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card border-danger">
                    <div class="card-header bg-danger text-white">
                        <h4 class="mb-0">Erro no Dashboard Executivo</h4>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-danger">
                            <strong>Erro:</strong> {str(e)}
                        </div>
                        <details>
                            <summary>Detalhes Técnicos</summary>
                            <pre class="mt-3 bg-light p-3 border rounded">{traceback.format_exc()}</pre>
                        </details>
                        <div class="mt-3">
                            <a href="/" class="btn btn-primary">Voltar ao Dashboard Principal</a>
                            <a href="/dashboard-simple" class="btn btn-secondary">Dashboard Simples</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''


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
