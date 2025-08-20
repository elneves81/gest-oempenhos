from app import app
from models import User

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        print(f"✅ Usuario admin existe")
        print(f"Username: {user.username}")
        print(f"Nome: {user.nome}")
        print(f"Ativo: {user.is_active}")
        print(f"Senha admin123 válida: {user.check_password('admin123')}")
    else:
        print("❌ Usuario admin NÃO encontrado")
        print("Criando usuário admin...")
        admin_user = User(
            username='admin',
            email='admin@sistema.local',
            nome='Administrador',
            is_active=True
        )
        admin_user.set_password('admin123')
        from models import db
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Usuario admin criado!")
