from flask import Blueprint, render_template, request, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from sqlalchemy import select, and_, or_, func
from werkzeug.utils import secure_filename
from datetime import datetime
import os, uuid

from models import db, User
from models_chat import ChatRoom, ChatMember, ChatRoomMessage, ChatAttachment

chat_offline = Blueprint('chat_offline', __name__, url_prefix='/chat-offline')

def is_admin():
    return bool(getattr(current_user, "is_admin", False))

def member_role(room_id, user_id):
    rec = db.session.execute(
        select(ChatMember.role).where(and_(ChatMember.room_id==room_id, ChatMember.user_id==user_id))
    ).scalar()
    return rec

def ensure_member(room_id, user_id, role_if_create="member"):
    role = member_role(room_id, user_id)
    if role: 
        return role
    # adiciona automaticamente se for grupo público (aqui consideramos todos os groups como públicos)
    db.session.add(ChatMember(room_id=room_id, user_id=user_id, role=role_if_create))
    db.session.commit()
    return role_if_create

@chat_offline.route('/')
@login_required
def index():
    """Lista salas do usuário + UI do chat."""
    # salas que o user participa
    rooms = db.session.execute(
        select(ChatRoom, ChatMember.role)
        .join(ChatMember, ChatMember.room_id==ChatRoom.id)
        .where(ChatMember.user_id==current_user.id)
        .order_by(ChatRoom.created_at.desc())
    ).all()

    # usuários (para iniciar DM ou criar grupo)
    users = db.session.execute(select(User.id, User.username)
               .where(User.id != current_user.id)
               .order_by(User.username.asc())).all()

    return render_template(
        'chat_offline/advanced.html',
        rooms=rooms,
        users=users
    )

# ---------- Salas ----------
@chat_offline.post('/rooms')
@login_required
def create_room():
    """Cria um grupo."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "Nome é obrigatório."}), 400

    room = ChatRoom(name=name, kind="group", created_by=current_user.id)
    db.session.add(room)
    db.session.flush()
    db.session.add(ChatMember(room_id=room.id, user_id=current_user.id, role="owner"))
    db.session.commit()
    return jsonify({"success": True, "room_id": room.id, "name": room.name, "kind": room.kind})

@chat_offline.post('/dm')
@login_required
def start_dm():
    """Abre/obtém DM (conversa particular) com outro usuário."""
    data = request.get_json() or {}
    uid = int(data.get("user_id", 0))
    if uid <= 0 or uid == current_user.id:
        return jsonify({"success": False, "error": "Usuário inválido."}), 400

    pair = sorted([current_user.id, uid])
    dm_key = f"{pair[0]}:{pair[1]}"

    room = db.session.execute(select(ChatRoom).where(and_(ChatRoom.kind=="dm", ChatRoom.dm_key==dm_key))).scalar()
    if not room:
        room = ChatRoom(name="Conversa privada", kind="dm", created_by=current_user.id, dm_key=dm_key)
        db.session.add(room)
        db.session.flush()
        db.session.add_all([
            ChatMember(room_id=room.id, user_id=pair[0], role="member"),
            ChatMember(room_id=room.id, user_id=pair[1], role="member"),
        ])
        db.session.commit()

    return jsonify({"success": True, "room_id": room.id, "kind": "dm"})

@chat_offline.get('/rooms')
@login_required
def list_rooms():
    rows = db.session.execute(
        select(ChatRoom.id, ChatRoom.name, ChatRoom.kind, ChatMember.role)
        .join(ChatMember, ChatMember.room_id==ChatRoom.id)
        .where(ChatMember.user_id==current_user.id)
        .order_by(ChatRoom.created_at.desc())
    ).mappings().all()
    return jsonify({"rooms": [dict(r) for r in rows]})

# ---------- Mensagens ----------
@chat_offline.post('/send_message')
@login_required
def send_message():
    """Envia texto e/ou anexo PDF para uma sala. Usuário comum não pode apagar/limpar."""
    room_id = int(request.form.get("room_id") or request.json.get("room") or 0)
    text = (request.form.get("text") or (request.json or {}).get("message") or "").strip()

    room = db.session.get(ChatRoom, room_id)
    if not room:
        return jsonify({"success": False, "error": "Sala não encontrada."}), 404

    role = ensure_member(room.id, current_user.id)  # garante participação

    msg = ChatRoomMessage(room_id=room.id, user_id=current_user.id, text=text or None)
    db.session.add(msg)
    db.session.flush()

    # Anexo (PDF apenas)
    files = request.files.getlist("file")
    ann = []
    for f in files:
        if not f.filename:
            continue
        name = secure_filename(f.filename)
        ext = os.path.splitext(name)[1].lower()
        mime = f.mimetype or "application/octet-stream"
        if ext not in {".pdf"} or mime not in {"application/pdf"}:
            continue  # ignora não‑PDF (ou retorne 400, se preferir)

        stored = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(request.app.config["UPLOAD_FOLDER"], stored)
        f.save(path)
        size = os.path.getsize(path)
        a = ChatAttachment(message_id=msg.id, filename=name, stored_name=stored, mime_type="application/pdf", size_bytes=size)
        db.session.add(a)
        ann.append(a)

    db.session.commit()

    payload = {
        "id": msg.id,
        "user_id": msg.user_id,
        "username": current_user.username,
        "text": msg.text,
        "created_at": msg.created_at.isoformat(),
        "room_id": room.id,
        "attachments": [{"id": a.id, "filename": a.filename, "size": a.size_bytes} for a in ann]
    }
    return jsonify({"success": True, "message": payload})

@chat_offline.get('/messages')
@login_required
def get_messages():
    """Lista mensagens de uma sala (paginações simples)."""
    room_id = int(request.args.get("room_id") or 0)
    page = max(int(request.args.get("page") or 1), 1)
    per = min(max(int(request.args.get("per") or 30), 10), 100)

    room = db.session.get(ChatRoom, room_id)
    if not room:
        return jsonify({"messages": []})

    if not member_role(room.id, current_user.id):
        return jsonify({"messages": []}), 403

    q = (db.session.query(ChatRoomMessage)
         .filter(ChatRoomMessage.room_id==room.id, ChatRoomMessage.deleted==False)
         .order_by(ChatRoomMessage.created_at.desc()))
    total = q.count()
    msgs = q.offset((page-1)*per).limit(per).all()
    msgs = list(reversed(msgs))  # mais antigos primeiro

    # carrega anexos
    ids = [m.id for m in msgs]
    atts = db.session.query(ChatAttachment).filter(ChatAttachment.message_id.in_(ids)).all()
    by_msg = {}
    for a in atts:
        by_msg.setdefault(a.message_id, []).append({"id": a.id, "filename": a.filename, "size": a.size_bytes})

    out = []
    users = {u.id: u.username for u in db.session.query(User).filter(User.id.in_([m.user_id for m in msgs])).all()}
    for m in msgs:
        out.append({
            "id": m.id,
            "user_id": m.user_id,
            "username": users.get(m.user_id, f"u{m.user_id}"),
            "text": m.text,
            "created_at": m.created_at.isoformat(),
            "attachments": by_msg.get(m.id, [])
        })

    return jsonify({"messages": out, "total": total, "page": page, "per": per})

# ---------- Download de anexo ----------
@chat_offline.get('/file/<int:att_id>')
@login_required
def download_file(att_id):
    a = db.session.get(ChatAttachment, att_id)
    if not a:
        abort(404)
    msg = db.session.get(ChatRoomMessage, a.message_id)
    if not msg:
        abort(404)
    if not member_role(msg.room_id, current_user.id):
        abort(403)
    folder = request.app.config["UPLOAD_FOLDER"]
    return send_from_directory(folder, a.stored_name, as_attachment=True, download_name=a.filename, mimetype=a.mime_type)

# ---------- Ações administrativas ----------
@chat_offline.post('/clear_room')
@login_required
def clear_room():
    """Limpa mensagens – apenas admin OU dono da sala."""
    data = request.get_json() or {}
    room_id = int(data.get('room') or 0)
    room = db.session.get(ChatRoom, room_id)
    if not room:
        return jsonify({'success': False, 'error': 'Sala não encontrada'}), 404

    role = member_role(room.id, current_user.id)
    if not (is_admin() or role == "owner"):
        return jsonify({'success': False, 'error': 'Sem permissão para limpar'}), 403

    db.session.query(ChatAttachment).filter(
        ChatAttachment.message_id.in_(db.session.query(ChatRoomMessage.id).filter(ChatRoomMessage.room_id==room.id))
    ).delete(synchronize_session=False)
    db.session.query(ChatRoomMessage).filter(ChatRoomMessage.room_id==room.id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True})
