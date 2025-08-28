#!/usr/bin/env python3
"""
Chat MSN Style com MySQL (XAMPP) - Porto 5002
Sistema de chat nostálgico integrado com banco MySQL
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

app = Flask(__name__)

# ===== CONFIGURAÇÃO =====
app.config['SECRET_KEY'] = 'chat-msn-secret-key-2024'

# MySQL Database - XAMPP (mesmo banco do sistema principal)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:@localhost:3306/chat_empenhos'
    '?charset=utf8mb4&autocommit=true'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Upload para anexos
app.config['UPLOAD_FOLDER'] = 'uploads_chat'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

# Inicializar extensões
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar o chat.'

# ===== MODELOS =====
class User(UserMixin, db.Model):
    """Usuário - compartilhado com sistema principal"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMsnRoom(db.Model):
    """Salas de chat MSN"""
    __tablename__ = 'chat_msn_room'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class ChatMsnMessage(db.Model):
    """Mensagens do chat MSN"""
    __tablename__ = 'chat_msn_message'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_msn_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, file, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='chat_messages')
    room = db.relationship('ChatMsnRoom', backref='messages')

class ChatMsnAttachment(db.Model):
    """Anexos do chat MSN"""
    __tablename__ = 'chat_msn_attachment'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chat_msn_message.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    message = db.relationship('ChatMsnMessage', backref='attachments')

# ===== LOGIN MANAGER =====
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== FUNÇÕES AUXILIARES =====
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Salva arquivo enviado e retorna informações"""
    if file and allowed_file(file.filename):
        # Gerar nome único
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Criar diretório se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Salvar arquivo
        file.save(filepath)
        
        return {
            'filename': filename,
            'original_filename': secure_filename(file.filename),
            'file_size': os.path.getsize(filepath),
            'file_type': ext
        }
    return None

# ===== ROTAS PRINCIPAIS =====
@app.route('/')
def index():
    """Página inicial - redireciona para chat se logado"""
    if current_user.is_authenticated:
        return redirect(url_for('chat_home'))
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat_home():
    """Página principal do chat MSN"""
    # Buscar salas ativas
    rooms = ChatMsnRoom.query.filter_by(is_active=True).order_by(ChatMsnRoom.created_at.desc()).all()
    return render_template('chat_msn_standalone.html', rooms=rooms)

# ===== ROTAS DE AUTENTICAÇÃO =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Bem-vindo ao Chat MSN!', 'success')
            return redirect(url_for('chat_home'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('login_chat.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do chat!', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return render_template('register_chat.html')
        
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado!', 'error')
            return render_template('register_chat.html')
        
        # Criar novo usuário
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada! Faça login para entrar no chat.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register_chat.html')

# ===== API DO CHAT =====
@app.route('/api/rooms')
@login_required
def api_rooms():
    """Lista salas de chat"""
    try:
        rooms = ChatMsnRoom.query.filter_by(is_active=True).order_by(ChatMsnRoom.created_at.desc()).all()
        
        results = []
        for room in rooms:
            # Contar mensagens
            msg_count = ChatMsnMessage.query.filter_by(room_id=room.id).count()
            
            results.append({
                'id': room.id,
                'name': room.name,
                'description': room.description,
                'created_at': room.created_at.isoformat(),
                'message_count': msg_count
            })
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/room/<int:room_id>/messages')
@login_required
def api_room_messages(room_id):
    """Busca mensagens de uma sala"""
    try:
        messages = ChatMsnMessage.query.filter_by(room_id=room_id)\
                                       .order_by(ChatMsnMessage.created_at.desc())\
                                       .limit(50).all()
        
        results = []
        for msg in messages:
            attachments = []
            for att in msg.attachments:
                attachments.append({
                    'id': att.id,
                    'filename': att.original_filename,
                    'file_size': att.file_size,
                    'file_type': att.file_type
                })
            
            results.append({
                'id': msg.id,
                'content': msg.content,
                'message_type': msg.message_type,
                'created_at': msg.created_at.isoformat(),
                'user': {
                    'id': msg.user.id,
                    'username': msg.user.username
                },
                'attachments': attachments
            })
        
        # Reverter para ordem cronológica
        results.reverse()
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/room/<int:room_id>/send', methods=['POST'])
@login_required
def api_send_message(room_id):
    """Envia mensagem para uma sala"""
    try:
        content = request.form.get('content', '').strip()
        file = request.files.get('file')
        
        if not content and not file:
            return jsonify({'success': False, 'error': 'Mensagem ou arquivo obrigatório'})
        
        # Verificar se sala existe
        room = ChatMsnRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'error': 'Sala não encontrada'})
        
        # Criar mensagem
        message = ChatMsnMessage(
            room_id=room_id,
            user_id=current_user.id,
            content=content or '[Arquivo anexado]',
            message_type='file' if file else 'text'
        )
        
        db.session.add(message)
        db.session.flush()  # Para obter o ID da mensagem
        
        # Processar arquivo se houver
        if file:
            file_info = save_uploaded_file(file)
            if file_info:
                attachment = ChatMsnAttachment(
                    message_id=message.id,
                    **file_info
                )
                db.session.add(attachment)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'message_type': message.message_type,
                'created_at': message.created_at.isoformat(),
                'user': {
                    'id': current_user.id,
                    'username': current_user.username
                }
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-room', methods=['POST'])
@login_required
def api_create_room():
    """Cria nova sala de chat"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Nome da sala obrigatório'})
        
        # Verificar se já existe
        existing = ChatMsnRoom.query.filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'error': 'Sala já existe'})
        
        # Criar sala
        room = ChatMsnRoom(
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(room)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'room': {
                'id': room.id,
                'name': room.name,
                'description': room.description,
                'created_at': room.created_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# ===== ARQUIVOS =====
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve arquivos enviados"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ===== INICIALIZAÇÃO =====
def create_chat_database():
    """Cria tabelas do chat"""
    with app.app_context():
        db.create_all()
        print("✅ Tabelas do chat criadas no MySQL!")
        
        # Criar sala padrão se não existir
        sala_geral = ChatMsnRoom.query.filter_by(name='Geral').first()
        if not sala_geral:
            # Buscar admin ou criar usuário padrão
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@localhost.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)
                db.session.flush()
            
            sala_geral = ChatMsnRoom(
                name='Geral',
                description='Sala geral para conversas',
                created_by=admin.id
            )
            db.session.add(sala_geral)
            db.session.commit()
            print("✅ Sala 'Geral' criada!")

if __name__ == '__main__':
    # Criar diretório de uploads
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("💬 CHAT MSN STYLE - MYSQL")
    print("=" * 40)
    print("🎨 Interface: http://localhost:5002/chat")
    print("🔐 Login: http://localhost:5002/login")
    print("💾 Banco: MySQL (XAMPP)")
    print("📎 Anexos: PDF, DOC, IMG")
    print("=" * 40)
    
    # Tentar criar tabelas
    try:
        create_chat_database()
    except Exception as e:
        print(f"⚠️  Erro ao criar tabelas: {e}")
        print("Certifique-se que o MySQL está rodando!")
    
    # Iniciar aplicação
    app.run(host='0.0.0.0', port=5002, debug=True)
