#!/usr/bin/env python3
"""
Script para criar usuário administrador
"""

from app import app, db
from models import User

def criar_admin():
    with app.app_context():
        try:
            # Verificar se admin existe
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print(f"✅ Usuário admin já existe: {admin.nome}")
                print(f"   Email: {admin.email}")
                print(f"   Status: {'Ativo' if admin.is_active else 'Inativo'}")
                print(f"   Admin: {'Sim' if admin.is_admin else 'Não'}")
                return
            
            # Criar usuário admin
            print("🔧 Criando usuário administrador...")
            
            new_admin = User(
                nome='Administrador Municipal',
                username='admin',
                email='admin@prefeitura.gov.br',
                is_admin=True,
                is_active=True
            )
            new_admin.set_password('admin123')
            
            db.session.add(new_admin)
            db.session.commit()
            
            print("✅ Usuário administrador criado com sucesso!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   Nome: Administrador Municipal")
            print("   Email: admin@prefeitura.gov.br")
            
        except Exception as e:
            print(f"❌ Erro ao criar admin: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_admin()
