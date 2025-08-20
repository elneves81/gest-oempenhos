# App package
from flask import Flask

def create_app():
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = 'empenhos-municipal-guarapuava-2025-sistema-robusto-sessao-permanente-admin123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Importar modelos e extensões
    from models import db
    db.init_app(app)
    
    # Importar e registrar blueprints
    from app.blueprints import contratos, empenhos, notas, relatorios
    
    app.register_blueprint(contratos.bp)
    app.register_blueprint(empenhos.bp)
    app.register_blueprint(notas.bp)
    app.register_blueprint(relatorios.bp)
    
    return app
