from flask import Blueprint, render_template, request, jsonify, send_from_directory, abort, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, User
from models_chat_rooms import ChatRoom, ChatMember, ChatRoomMessage
from datetime import datetime
import uuid
import os

# Blueprint para chat offline
chat_offline = Blueprint('chat_offline', __name__, url_prefix='/chat-offline')

# Autocheck para garantir que o schema está correto
def _ensure_chat_schema():
    """Garante que as colunas necessárias existem"""
    from sqlalchemy import text
    try:
        cols = db.session.execute(text("PRAGMA table_info(chat_rooms)")).mappings().all()
        names = [c["name"] for c in cols]
        changed = False
        if "kind" not in names:
            db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN kind TEXT NOT NULL DEFAULT 'group'"))
            changed = True
        if "dm_key" not in names:
            db.session.execute(text("ALTER TABLE chat_rooms ADD COLUMN dm_key TEXT"))
            changed = True
        if changed:
            db.session.commit()
            print("✅ Schema do chat atualizado automaticamente")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível verificar schema do chat: {e}")

# Helpers para compatibilidade de campos de mensagem
def _get_msg_text_field():
    """Retorna o atributo correto do modelo (content ou text)"""
    if hasattr(ChatRoomMessage, "content"):
        return "content"
    return "text"

def _get_msg_text_value(m):
    """Extrai o texto da mensagem independente do campo usado"""
    return getattr(m, "content", None) or getattr(m, "text", None) or ""

def is_member(room_id, user_id):
    """Verifica se o usuário é membro da sala"""
    return ChatMember.query.filter_by(room_id=room_id, user_id=user_id).first() is not None

def ensure_member(room_id, user_id):
    """Garante que o usuário seja membro da sala"""
    if not is_member(room_id, user_id):
        member = ChatMember(room_id=room_id, user_id=user_id, role='member')
        db.session.add(member)
        db.session.commit()

def get_or_create_dm(user_a_id, user_b_id):
    """Cria ou retorna DM entre dois usuários (versão única)"""
    a, b = sorted([user_a_id, user_b_id])
    key = f"dm:{a}:{b}"
    
    dm = ChatRoom.query.filter_by(dm_key=key).first()
    if dm:
        return dm
    
    # Criar novo DM
    dm = ChatRoom(
        name=f"DM",
        kind="dm",
        dm_key=key,
        created_by=user_a_id
    )
    db.session.add(dm)
    db.session.flush()  # para ter o ID
    
    # Adicionar membros
    member1 = ChatMember(room_id=dm.id, user_id=a, role="member")
    member2 = ChatMember(room_id=dm.id, user_id=b, role="member")
    db.session.add_all([member1, member2])
    db.session.commit()
    
    return dm

@chat_offline.route('/')
@login_required
def index():
    """Página principal do chat offline"""
    # Garantir schema atualizado
    _ensure_chat_schema()
    
    # Criar ou buscar sala geral
    geral_room = ChatRoom.query.filter_by(name='Chat Geral', kind='group').first()
    if not geral_room:
        geral_room = ChatRoom(name='Chat Geral', kind='group', created_by=current_user.id)
        db.session.add(geral_room)
        db.session.flush()
    
    # Garantir que o usuário seja membro
    ensure_member(geral_room.id, current_user.id)
    
    # Buscar mensagens recentes
    messages_query = (
        db.session.query(ChatRoomMessage, User)
        .join(User, User.id == ChatRoomMessage.user_id)
        .filter(ChatRoomMessage.room_id == geral_room.id)
        .filter(ChatRoomMessage.deleted == False)
        .order_by(ChatRoomMessage.created_at.desc())
        .limit(100)
    )
    
    messages = []
    for msg, user in messages_query.all():
        messages.append({
            'id': msg.id,
            'user_id': user.id,
            'username': user.nome or user.username or user.email,
            'message': _get_msg_text_value(msg),
            'timestamp': msg.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'room': 'geral'
        })
    
    messages.reverse()  # Mais antigas primeiro
    
    # Buscar usuários online (membros da sala)
    online_users = []
    members = db.session.query(ChatMember, User).join(User).filter(
        ChatMember.room_id == geral_room.id
    ).all()
    
    for member, user in members:
        online_users.append({
            'id': user.id,
            'username': user.nome or user.username or user.email
        })
    
    return render_template('chat_offline/fixed.html', 
                         messages=messages,
                         online_users=online_users,
                         current_room='geral')

# ✅ Rotas REST "canônicas"

@chat_offline.route('/rooms/<int:room_id>/messages')
@login_required
def list_messages_room(room_id):
    """GET /rooms/<room_id>/messages - Listar mensagens da sala"""
    if not is_member(room_id, current_user.id):
        return jsonify(error="not_a_member"), 403

    q = (
        db.session.query(ChatRoomMessage, User)
        .join(User, User.id == ChatRoomMessage.user_id)
        .filter(ChatRoomMessage.room_id == room_id)
        .order_by(ChatRoomMessage.created_at.asc())
    )
    if hasattr(ChatRoomMessage, "deleted"):
        q = q.filter(ChatRoomMessage.deleted == False)

    rows = q.all()
    data = [{
        "id": m.id,
        "room_id": room_id,
        "user_id": m.user_id,
        "username": u.nome or u.username or u.email,
        "content": _get_msg_text_value(m),
        "created_at": (m.created_at or datetime.utcnow()).isoformat()
    } for (m, u) in rows]

    return jsonify(messages=data)


@chat_offline.route('/rooms/<int:room_id>/messages', methods=['POST'])
@login_required
def post_message_room(room_id):
    """POST /rooms/<room_id>/messages - Enviar mensagem para sala"""
    if not is_member(room_id, current_user.id):
        # entra automaticamente no grupo/DM
        ensure_member(room_id, current_user.id)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or data.get("text") or data.get("message") or "").strip()
    if not content:
        return jsonify(error="empty"), 400

    field = _get_msg_text_field()
    payload = {
        "room_id": room_id,
        "user_id": current_user.id,
        "created_at": datetime.utcnow()
    }
    payload[field] = content

    msg = ChatRoomMessage(**payload)
    db.session.add(msg)
    db.session.commit()

    return jsonify(
        id=msg.id,
        room_id=room_id,
        user_id=current_user.id,
        username=current_user.nome or current_user.username or current_user.email,
        content=content,
        created_at=msg.created_at.isoformat()
    )

# ♻️ Compatibilidade com rotas antigas

@chat_offline.route('/messages')
@login_required
def get_messages():
    """Compatibilidade: /messages → chama a nova rota"""
    room_id = int(request.args.get("room_id") or 0)
    if not room_id:
        return jsonify(messages=[])
    return list_messages_room(room_id)


@chat_offline.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Compatibilidade: /send_message → chama a nova rota"""
    # Tentar obter room_id de diferentes fontes
    room_id = None
    if request.is_json:
        data = request.get_json() or {}
        room_id = data.get("room_id") or data.get("room")
        text = data.get("message") or data.get("content") or data.get("text")
    else:
        room_id = request.form.get("room_id") or request.form.get("room")
        text = request.form.get("text") or request.form.get("message")
    
    # Se for texto simples, converter para numérico
    try:
        room_id = int(room_id) if room_id else 0
    except (ValueError, TypeError):
        room_id = 0
    
    if not room_id:
        return jsonify(success=False, error="room_id é obrigatório"), 400

    text = (text or "").strip()
    if not text:
        return jsonify(success=False, error="mensagem vazia"), 400

    # Preparar dados para a nova rota
    original_json = getattr(request, '_cached_json', None)
    request._cached_json = {"content": text}
    
    try:
        result = post_message_room(room_id)
        # Converter resposta para formato esperado pela rota antiga
        if result.status_code == 200:
            data = result.get_json()
            return jsonify(success=True, message=data)
        else:
            return jsonify(success=False, error=result.get_json().get('error', 'Erro desconhecido'))
    finally:
        # Restaurar JSON original
        if original_json is not None:
            request._cached_json = original_json
        elif hasattr(request, '_cached_json'):
            delattr(request, '_cached_json')

@chat_offline.route('/get_messages')
@login_required
def get_messages_legacy():
    """Buscar mensagens de uma sala - compatibilidade com frontend"""
    room_name = request.args.get('room', 'geral')
    last_id = request.args.get('last_id', 0, type=int)
    
    # Buscar ou criar sala
    room = ChatRoom.query.filter_by(name=f'Chat {room_name.title()}', kind='group').first()
    if not room:
        # Criar sala se não existir
        room = ChatRoom(name=f'Chat {room_name.title()}', kind='group')
        db.session.add(room)
        db.session.commit()
    
    # Garantir que o usuário seja membro
    ensure_member(room.id, current_user.id)
    
    # Buscar mensagens
    query = ChatRoomMessage.query.filter_by(room_id=room.id, deleted=False)
    if last_id > 0:
        query = query.filter(ChatRoomMessage.id > last_id)
    
    messages = query.join(User).order_by(ChatRoomMessage.created_at.desc()).limit(50).all()
    
    msg_list = []
    for msg in messages:
        msg_text = _get_msg_text_value(msg)
        msg_list.append({
            'id': msg.id,
            'content': msg_text,
            'text': msg_text,  # compatibilidade
            'message': msg_text,  # compatibilidade
            'user': msg.user.nome or msg.user.username,
            'timestamp': msg.created_at.strftime('%H:%M'),
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({'messages': msg_list})

@chat_offline.route('/get_users')
@login_required
def get_users():
    """Buscar usuários online - compatibilidade"""
    room_id = request.args.get('room_id')
    if not room_id:
        # Buscar sala geral para compatibilidade
        geral_room = ChatRoom.query.filter_by(name='Chat Geral', kind='group').first()
        if not geral_room:
            return jsonify({'users': []})
        room_id = geral_room.id
    
    try:
        room_id = int(room_id)
    except (ValueError, TypeError):
        return jsonify({'users': []})
    
    if not is_member(room_id, current_user.id):
        return jsonify({'users': []})

    online_users = []
    members = db.session.query(ChatMember, User).join(User).filter(
        ChatMember.room_id == room_id
    ).all()
    
    for member, user in members:
        online_users.append({
            'id': user.id,
            'username': user.nome or user.username or user.email,
            'is_current': user.id == current_user.id
        })
    
    return jsonify({'users': online_users})

@chat_offline.route('/leave_room', methods=['POST'])
@login_required
def leave_room():
    """Sair de uma sala"""
    data = request.get_json() or {}
    room_id = data.get('room_id') or data.get('room')
    
    try:
        room_id = int(room_id) if room_id else 0
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'room_id inválido'}), 400
    
    if room_id:
        member = ChatMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
        if member:
            db.session.delete(member)
            db.session.commit()
    
    return jsonify({'success': True})

@chat_offline.route('/clear_room', methods=['POST'])
@login_required
def clear_room():
    """Limpar mensagens de uma sala (apenas para admin)"""
    # Verificar se é admin de forma segura
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin:
        return jsonify({'success': False, 'error': 'Apenas administradores podem limpar o chat'}), 403
    
    data = request.get_json() or {}
    room_id = data.get('room_id') or data.get('room')
    
    try:
        room_id = int(room_id) if room_id else 0
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'room_id inválido'}), 400
    
    if room_id:
        # Marcar mensagens como deletadas ao invés de apagar
        ChatRoomMessage.query.filter_by(room_id=room_id).update({'deleted': True})
        db.session.commit()
    
    return jsonify({'success': True})

# 🗂️ Download/anexo - correção current_app
@chat_offline.route('/download/<filename>')
@login_required  
def download_file(filename):
    """Download de arquivo anexado ao chat"""
    try:
        folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        return send_from_directory(folder, filename, as_attachment=True)
    except Exception as e:
        return abort(404)

@chat_offline.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Servir arquivo anexado ao chat"""
    try:
        folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        return send_from_directory(folder, filename)
    except Exception as e:
        return abort(404)

@chat_offline.route('/test')
@login_required
def test_page():
    """Página de teste das rotas padronizadas"""
    return render_template('chat_test.html')
