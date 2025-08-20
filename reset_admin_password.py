#!/usr/bin/env python3
"""Script para resetar senha do admin"""

import sys
sys.path.append('.')

# Importar app corretamente
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

def reset_admin_password():
    """Reseta a senha do usuário admin para 'admin123'"""
    with app.app_context():
        from models import User, db
        
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            admin_user.set_password('admin123')
            db.session.commit()
            print("✅ Senha do admin resetada para: admin123")
            print("🔐 Use: Username: admin | Senha: admin123")
        else:
            print("❌ Usuário admin não encontrado")

if __name__ == "__main__":
    reset_admin_password()
