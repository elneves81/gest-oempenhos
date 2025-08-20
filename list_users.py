#!/usr/bin/env python3
"""Script para listar usuários do sistema"""

import sys
sys.path.append('.')

# Importar app corretamente
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

def list_users():
    """Lista todos os usuários do sistema"""
    with app.app_context():
        from models import User
        
        print("👥 Usuários cadastrados no sistema:")
        users = User.query.all()
        
        if not users:
            print("❌ Nenhum usuário encontrado no banco de dados")
            return
            
        for user in users:
            print(f"📋 ID: {user.id}")
            print(f"   👤 Username: {user.username}")
            print(f"   📧 Email: {user.email}")
            print(f"   🔑 Admin: {'Sim' if user.is_admin else 'Não'}")
            print(f"   ✅ Ativo: {'Sim' if user.is_active else 'Não'}")
            print("-" * 40)
            
        print(f"\n🔍 Total de usuários: {len(users)}")

if __name__ == "__main__":
    list_users()
