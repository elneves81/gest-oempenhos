#!/usr/bin/env python3
"""
Script para debugar as rotas registradas no Flask
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from datetime import datetime

# Configuração mínima da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = 'debug-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///empenhos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar database
from models import db
db.init_app(app)

# Importar blueprints
try:
    from routes.contratos import contratos_bp
    app.register_blueprint(contratos_bp, url_prefix='/contratos')
    print("✅ Blueprint contratos importado e registrado")
except Exception as e:
    print(f"❌ Erro ao importar contratos blueprint: {e}")

def list_routes():
    """Lista todas as rotas registradas"""
    print("🔍 ROTAS REGISTRADAS NO FLASK")
    print("=" * 50)
    
    rules = []
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        rules.append((rule.endpoint, methods, str(rule)))
    
    # Ordenar por endpoint
    rules.sort(key=lambda x: x[0])
    
    anexos_routes = []
    for endpoint, methods, rule in rules:
        if 'anexos' in rule.lower():
            anexos_routes.append((endpoint, methods, rule))
            print(f"📎 {endpoint:30} {methods:15} {rule}")
        
    print(f"\n📊 Total de rotas: {len(rules)}")
    print(f"📎 Rotas de anexos: {len(anexos_routes)}")
    
    # Verificar especificamente a rota que está falhando
    target_route = "/contratos/<int:contrato_id>/anexos"
    print(f"\n🎯 Procurando rota: {target_route}")
    
    found = False
    for endpoint, methods, rule in rules:
        if 'anexos' in rule and 'contrato_id' in rule:
            print(f"✅ ENCONTRADA: {endpoint} | {methods} | {rule}")
            found = True
    
    if not found:
        print("❌ ROTA NÃO ENCONTRADA!")
        print("\n🔍 Rotas de contratos disponíveis:")
        for endpoint, methods, rule in rules:
            if 'contratos' in rule.lower():
                print(f"   {endpoint:30} {methods:15} {rule}")

if __name__ == "__main__":
    with app.app_context():
        list_routes()
