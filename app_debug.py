#!/usr/bin/env python3
"""
🔧 APLICAÇÃO EMPENHOS - VERSÃO DEBUG
=====================================
Versão simplificada para diagnóstico
"""

from flask import Flask, render_template, redirect, url_for, flash, request
from waitress import serve
import logging
import os

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuração da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.before_request
def log_request():
    logger.info(f"📥 Requisição: {request.method} {request.path}")

@app.after_request
def after_request(response):
    if response.mimetype.startswith('text/html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
    logger.info(f"📤 Resposta: {response.status_code} - {response.mimetype}")
    return response

@app.errorhandler(404)
def not_found(error):
    logger.error(f"❌ 404: {request.path}")
    return "Página não encontrada", 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ 500: {error}")
    return f"Erro interno: {error}", 500

@app.route('/')
def home():
    logger.info("🏠 Renderizando dashboard simples")
    try:
        return render_template('dashboard_simple.html')
    except Exception as e:
        logger.error(f"❌ Erro ao renderizar dashboard: {e}")
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Erro Debug</title>
        </head>
        <body>
            <h1>❌ Erro na Aplicação</h1>
            <p>Erro: {e}</p>
        </body>
        </html>
        """, 500

@app.route('/debug')
def debug_info():
    logger.info("🔍 Informações de debug")
    try:
        import flask
        flask_version = flask.__version__
    except:
        flask_version = "Desconhecida"
        
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Debug Info</title>
    </head>
    <body>
        <h1>🔍 Informações de Debug</h1>
        <ul>
            <li>Flask Version: {flask_version}</li>
            <li>Template Folder: {app.template_folder}</li>
            <li>Static Folder: {app.static_folder}</li>
            <li>Instance Path: {app.instance_path}</li>
            <li>Working Directory: {os.getcwd()}</li>
        </ul>
    </body>
    </html>
    """

@app.route('/test-template')
def test_template():
    logger.info("🧪 Testando template base")
    try:
        return render_template('base.html')
    except Exception as e:
        logger.error(f"❌ Erro no template base: {e}")
        return f"Erro no template: {e}", 500

if __name__ == '__main__':
    print("🔧 APLICAÇÃO EMPENHOS - DEBUG")
    print("=" * 40)
    print("📍 Endereços:")
    print("   • http://localhost:8001")
    print("   • http://127.0.0.1:8001") 
    print("   • http://10.0.50.79:8001")
    print("📋 Rotas disponíveis:")
    print("   • / - Dashboard")
    print("   • /debug - Informações")
    print("   • /test-template - Teste template")
    print("=" * 40)
    
    try:
        logger.info("🚀 Iniciando servidor Waitress debug")
        serve(app, host='0.0.0.0', port=8001, threads=2)
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar: {e}")
        print(f"❌ ERRO: {e}")
