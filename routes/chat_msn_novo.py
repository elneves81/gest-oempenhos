from flask import Blueprint, render_template, request, jsonify, send_from_directory, abort, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, User
from models_chat_msn_novo import ChatMsnRoom, ChatMsnMember, ChatMsnMessage, ChatMsnAttachment
from datetime import datetime
import uuid
import os
from werkzeug.utils import secure_filename

# Blueprint para chat MSN Style novo
chat_msn = Blueprint('chat_msn', __name__, url_prefix='/chat-msn')

# Configurações de upload
UPLOAD_FOLDER = 'uploads/chat_msn'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_member(room_id, user_id):
    """Verifica se o usuário é membro da sala"""
    return ChatMsnMember.query.filter_by(room_id=room_id, user_id=user_id).first() is not None

def ensure_member(room_id, user_id):
    """Garante que o usuário seja membro da sala"""
    if not is_member(room_id, user_id):
        member = ChatMsnMember(room_id=room_id, user_id=user_id, role='member')
        db.session.add(member)
        db.session.commit()

def _ensure_chat_msn_schema():
    """Garante que as tabelas MSN existem"""
    from sqlalchemy import text
    try:
        # Criar tabelas MSN
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_msn_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'group',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dm_key TEXT UNIQUE
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_msn_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES chat_msn_rooms (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(room_id, user_id)
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_msn_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0,
                FOREIGN KEY (room_id) REFERENCES chat_msn_rooms (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_msn_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES chat_msn_messages (id)
            )
        """))
        
        db.session.commit()
        print("✅ Tabelas Chat MSN criadas com sucesso!")
        
    except Exception as e:
        print(f"⚠️ Erro ao criar tabelas MSN: {e}")

@chat_msn.route('/')
@login_required
def index():
    """Página principal do chat MSN Style"""
    _ensure_chat_msn_schema()
    
    # Buscar ou criar sala geral MSN
    geral_room = ChatMsnRoom.query.filter_by(name='Chat MSN Geral', kind='group').first()
    if not geral_room:
        geral_room = ChatMsnRoom(name='Chat MSN Geral', kind='group', created_by=current_user.id)
        db.session.add(geral_room)
        db.session.flush()
    
    # Garantir que o usuário seja membro
    ensure_member(geral_room.id, current_user.id)
    
    # Buscar mensagens recentes com anexos
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
        # Buscar anexos da mensagem
        attachments = ChatMsnAttachment.query.filter_by(message_id=msg.id).all()
        
        messages.append({
            'id': msg.id,
            'user_id': user.id,
            'username': user.nome or user.username or user.email,
            'message': msg.content or '',
            'message_type': msg.message_type or 'text',
            'timestamp': msg.created_at.strftime('%d/%m/%Y %H:%M'),
            'attachments': [att.to_dict() for att in attachments]
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

@chat_msn.route('/rooms/<int:room_id>/messages')
@login_required
def list_messages_room(room_id):
    """GET /rooms/<room_id>/messages - Listar mensagens da sala"""
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
        # Buscar anexos
        attachments = ChatMsnAttachment.query.filter_by(message_id=m.id).all()
        
        data.append({
            "id": m.id,
            "room_id": room_id,
            "user_id": m.user_id,
            "username": u.nome or u.username or u.email,
            "content": m.content or '',
            "message_type": m.message_type or 'text',
            "created_at": (m.created_at or datetime.utcnow()).isoformat(),
            "attachments": [att.to_dict() for att in attachments]
        })

    return jsonify(messages=data)

@chat_msn.route('/rooms/<int:room_id>/messages', methods=['POST'])
@login_required
def post_message_room(room_id):
    """POST /rooms/<room_id>/messages - Enviar mensagem para sala"""
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

@chat_msn.route('/rooms/<int:room_id>/upload', methods=['POST'])
@login_required
def upload_file_to_room(room_id):
    """POST /rooms/<room_id>/upload - Upload de arquivo para sala"""
    if not is_member(room_id, current_user.id):
        ensure_member(room_id, current_user.id)
    
    if 'file' not in request.files:
        return jsonify(error="no_file"), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="no_filename"), 400
    
    if not allowed_file(file.filename):
        return jsonify(error="file_type_not_allowed"), 400
    
    # Verificar tamanho do arquivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify(error="file_too_large"), 400
    
    try:
        # Preparar diretório
        upload_dir = os.path.join(current_app.root_path, UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Gerar nome único
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Salvar arquivo
        file.save(file_path)
        
        # Detectar tipo MIME
        content_type = file.content_type or 'application/octet-stream'
        if original_filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif original_filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif original_filename.lower().endswith('.png'):
            content_type = 'image/png'
        
        # Criar mensagem com anexo
        msg = ChatMsnMessage(
            room_id=room_id,
            user_id=current_user.id,
            content=f"📎 {original_filename}",
            message_type='file',
            created_at=datetime.utcnow()
        )
        
        db.session.add(msg)
        db.session.flush()  # Para obter o ID
        
        # Criar anexo
        attachment = ChatMsnAttachment(
            message_id=msg.id,
            filename=unique_filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            file_path=file_path,
            uploaded_at=datetime.utcnow()
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return jsonify(
            id=msg.id,
            room_id=room_id,
            user_id=current_user.id,
            username=current_user.nome or current_user.username or current_user.email,
            content=msg.content,
            message_type='file',
            created_at=msg.created_at.isoformat(),
            attachments=[attachment.to_dict()]
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no upload: {e}")
        return jsonify(error="upload_failed"), 500

@chat_msn.route('/attachments/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    """Download de anexo"""
    attachment = ChatMsnAttachment.query.get_or_404(attachment_id)
    
    # Verificar se o usuário tem acesso à mensagem
    message = ChatMsnMessage.query.get(attachment.message_id)
    if not message or not is_member(message.room_id, current_user.id):
        abort(403)
    
    # Verificar se o arquivo existe
    if not os.path.exists(attachment.file_path):
        abort(404)
    
    directory = os.path.dirname(attachment.file_path)
    filename = os.path.basename(attachment.file_path)
    
    return send_from_directory(
        directory, 
        filename, 
        as_attachment=True,
        download_name=attachment.original_filename
    )

@chat_msn.route('/rooms')
@login_required
def list_rooms():
    """Listar salas disponíveis"""
    # Salas que o usuário é membro
    user_rooms = (
        db.session.query(ChatMsnRoom)
        .join(ChatMsnMember)
        .filter(ChatMsnMember.user_id == current_user.id)
        .all()
    )
    
    rooms = [room.to_dict() for room in user_rooms]
    return jsonify(rooms=rooms)

@chat_msn.route('/rooms/<int:room_id>')
@login_required
def get_room_info(room_id):
    """Informações de uma sala específica"""
    if not is_member(room_id, current_user.id):
        abort(403)
    
    room = ChatMsnRoom.query.get_or_404(room_id)
    
    # Membros da sala
    members = (
        db.session.query(User, ChatMsnMember)
        .join(ChatMsnMember)
        .filter(ChatMsnMember.room_id == room_id)
        .all()
    )
    
    room_data = room.to_dict()
    room_data['members'] = [
        {
            'user_id': user.id,
            'username': user.nome or user.username or user.email,
            'role': member.role,
            'joined_at': member.joined_at.isoformat()
        }
        for user, member in members
    ]
    
    return jsonify(room_data)

# Criar diretório de upload se não existir
def init_upload_dir(app):
    upload_path = os.path.join(app.root_path, UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)
