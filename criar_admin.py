#!/usr/bin/env python3
"""
Script para criar usuário padrão
"""

import importlib.util
import sys

# Importar especificamente o arquivo app.py
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

from models import db, User
from werkzeug.security import generate_password_hash

def criar_usuario_padrao():
    """Cria usuário padrão se não existir"""
    with app_module.app.app_context():
        # Verificar se já existe admin
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # Criar usuário admin
            admin = User(
                username='admin',
                nome='Administrador',
                email='admin@empenhos.gov.br',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado com sucesso!")
            print("   Login: admin")
            print("   Senha: admin123")
        else:
            print("✅ Usuário admin já existe")
            print("   Login: admin")
            print("   Senha: admin123")

if __name__ == '__main__':
    criar_usuario_padrao()
