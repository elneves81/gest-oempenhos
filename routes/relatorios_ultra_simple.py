# relatorios.py - VERSÃO ULTRA SIMPLIFICADA
from flask import Blueprint
from flask_login import login_required

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/')
@login_required
def index():
    """Dashboard de relatórios - TESTE MÍNIMO"""
    return '''
    <h1>✅ RELATÓRIOS FUNCIONANDO!</h1>
    <p>Esta é a versão mais simples possível.</p>
    <p>Nenhum acesso ao banco de dados.</p>
    '''
