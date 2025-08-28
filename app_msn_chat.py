#!/usr/bin/env python3
"""
App MSN Chat - Servidor independente para o Chat MSN Style
"""

from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
import os

# Criar app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'msn-chat-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_msn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensões
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo de usuário simples para teste
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_active(self):
        return True
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelos MSN - definidos inline para evitar imports
class ChatMsnRoom(db.Model):
    __tablename__ = "chat_msn_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    kind = db.Column(db.String(20), nullable=False, default="group")
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    dm_key = db.Column(db.String(64), unique=True, nullable=True)

class ChatMsnMember(db.Model):
    __tablename__ = "chat_msn_members"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_msn_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

class ChatMsnMessage(db.Model):
    __tablename__ = "chat_msn_messages"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_msn_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(20), default="text", nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)

# Registrar blueprint do chat MSN
from flask import jsonify, request
from flask_login import login_user
from datetime import datetime

# Funções auxiliares
def is_member(room_id, user_id):
    return ChatMsnMember.query.filter_by(room_id=room_id, user_id=user_id).first() is not None

def ensure_member(room_id, user_id):
    if not is_member(room_id, user_id):
        member = ChatMsnMember(room_id=room_id, user_id=user_id, role='member')
        db.session.add(member)
        db.session.commit()

# Rotas do chat MSN
@app.route('/chat-msn/')
@login_required
def chat_msn_index():
    """Página principal do chat MSN Style"""
    # Buscar ou criar sala geral MSN
    geral_room = ChatMsnRoom.query.filter_by(name='Chat MSN Geral', kind='group').first()
    if not geral_room:
        geral_room = ChatMsnRoom(name='Chat MSN Geral', kind='group', created_by=current_user.id)
        db.session.add(geral_room)
        db.session.flush()
    
    # Garantir que o usuário seja membro
    ensure_member(geral_room.id, current_user.id)
    
    # Buscar mensagens recentes
    messages_query = (
        db.session.query(ChatMsnMessage, User)
        .join(User, User.id == ChatMsnMessage.user_id)
        .filter(ChatMsnMessage.room_id == geral_room.id)
        .filter(ChatMsnMessage.deleted == False)
        .order_by(ChatMsnMessage.created_at.desc())
        .limit(50)
    )
    
    messages = []
    for msg, user in messages_query.all():
        messages.append({
            'id': msg.id,
            'user_id': user.id,
            'username': user.nome or user.username or user.email,
            'message': msg.content or '',
            'message_type': msg.message_type or 'text',
            'timestamp': msg.created_at.strftime('%d/%m/%Y %H:%M'),
            'attachments': []  # Sem anexos por enquanto
        })
    
    messages.reverse()  # Mais antigas primeiro
    
    # Buscar usuários online
    online_users = []
    members = db.session.query(ChatMsnMember, User).join(User).filter(
        ChatMsnMember.room_id == geral_room.id
    ).all()
    
    for member, user in members:
        online_users.append({
            'id': user.id,
            'username': user.nome or user.username or user.email
        })
    
    return render_template('chat_msn_standalone.html', 
                         messages=messages,
                         online_users=online_users,
                         current_room='geral',
                         current_room_id=geral_room.id,
                         current_room_name='Chat MSN Geral')

@app.route('/chat-msn/rooms/<int:room_id>/messages')
@login_required
def list_messages_room(room_id):
    """Listar mensagens da sala"""
    if not is_member(room_id, current_user.id):
        return jsonify(error="not_a_member"), 403

    q = (
        db.session.query(ChatMsnMessage, User)
        .join(User, User.id == ChatMsnMessage.user_id)
        .filter(ChatMsnMessage.room_id == room_id)
        .filter(ChatMsnMessage.deleted == False)
        .order_by(ChatMsnMessage.created_at.asc())
    )

    rows = q.all()
    data = []
    
    for (m, u) in rows:
        data.append({
            "id": m.id,
            "room_id": room_id,
            "user_id": m.user_id,
            "username": u.nome or u.username or u.email,
            "content": m.content or '',
            "message_type": m.message_type or 'text',
            "created_at": (m.created_at or datetime.utcnow()).isoformat(),
            "attachments": []
        })

    return jsonify(messages=data)

@app.route('/chat-msn/rooms/<int:room_id>/messages', methods=['POST'])
@login_required
def post_message_room(room_id):
    """Enviar mensagem para sala"""
    if not is_member(room_id, current_user.id):
        ensure_member(room_id, current_user.id)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or data.get("text") or data.get("message") or "").strip()
    
    if not content:
        return jsonify(error="empty"), 400

    # Criar mensagem
    msg = ChatMsnMessage(
        room_id=room_id,
        user_id=current_user.id,
        content=content,
        message_type='text',
        created_at=datetime.utcnow()
    )
    
    db.session.add(msg)
    db.session.commit()

    return jsonify(
        id=msg.id,
        room_id=room_id,
        user_id=current_user.id,
        username=current_user.nome or current_user.username or current_user.email,
        content=content,
        message_type='text',
        created_at=msg.created_at.isoformat(),
        attachments=[]
    )

# Rota de login simples para teste
@app.route('/login')
def login():
    """Login de teste"""
    from flask_login import login_user
    # Para teste, fazer login automático como admin
    user = User.query.filter_by(username='admin').first()
    if user:
        login_user(user)
        return redirect('/chat-msn/')
    else:
        return "Usuário admin não encontrado. Execute python setup_msn_app.py primeiro."

@app.route('/')
def index():
    """Página inicial - redireciona para o chat"""
    if current_user.is_authenticated:
        return redirect('/chat-msn/')
    else:
        return redirect(url_for('login'))

def create_tables():
    """Criar tabelas e dados iniciais"""
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                nome='Administrador',
                email='admin@exemplo.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado (admin/admin123)")
        
        # Criar sala geral se não existir
        geral_room = ChatMsnRoom.query.filter_by(name='Chat MSN Geral').first()
        if not geral_room:
            geral_room = ChatMsnRoom(
                name='Chat MSN Geral',
                kind='group',
                created_by=admin.id
            )
            db.session.add(geral_room)
            db.session.commit()
            print("✅ Sala 'Chat MSN Geral' criada")

if __name__ == '__main__':
    print("🚀 Iniciando Chat MSN Style...")
    create_tables()
    print("🌐 Servidor rodando em: http://localhost:5002")
    print("🔐 Login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5002)
