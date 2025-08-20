#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para forçar a criação das tabelas do banco de dados
"""

import os
import sys

# Definir variáveis de ambiente necessárias
os.environ['FLASK_ENV'] = 'development'

# Importar direto do arquivo app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar Flask app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuração básica do Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Importar todos os modelos
from models import *

def criar_tabelas():
    """Força a criação de todas as tabelas"""
    with app.app_context():
        print("🗃️ Criando todas as tabelas...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar se as tabelas foram criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        print(f"📊 Tabelas criadas: {len(tabelas)}")
        for tabela in sorted(tabelas):
            print(f"  ✓ {tabela}")
            
        # Verificar estrutura da tabela contratos especificamente
        if 'contratos' in tabelas:
            colunas = inspector.get_columns('contratos')
            print(f"\n📋 Estrutura da tabela contratos ({len(colunas)} colunas):")
            
            colunas_responsavel = []
            for col in colunas:
                nome = col['name']
                if nome.startswith('responsavel_'):
                    colunas_responsavel.append(nome)
            
            print("📧 Colunas do responsável:")
            for col in sorted(colunas_responsavel):
                print(f"  ✓ {col}")
                
            # Verificar campos específicos
            novos_campos = ['responsavel_emails_extras', 'responsavel_telefones_extras']
            for campo in novos_campos:
                if campo in colunas_responsavel:
                    print(f"✅ Campo {campo} criado com sucesso!")
                else:
                    print(f"❌ Campo {campo} NÃO foi criado!")

if __name__ == "__main__":
    criar_tabelas()
