# models_chat.py
from datetime import datetime
from werkzeug.security import gen_salt
from models import db

# Modelos originais para Chat IA (mantidos para compatibilidade)
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    session_id = db.Column(db.String(100), index=True, nullable=False)

    user = db.relationship('User', backref=db.backref('chat_messages', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Usuário',
            'message': self.message,
            'response': self.response,
            'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M'),
            'session_id': self.session_id,
        }


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='Nova Conversa', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('chat_sessions', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'last_message_at': self.last_message_at.strftime('%d/%m/%Y %H:%M'),
        }

# Novos modelos para Chat Interno com grupos, DMs e anexos
class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    kind = db.Column(db.String(20), nullable=False, default="group")  # 'group' | 'dm'
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # para DM: hash com users ordenados ("u1:u7")
    dm_key = db.Column(db.String(64), unique=True, nullable=True)

class ChatMember(db.Model):
    __tablename__ = "chat_members"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member")  # 'owner' | 'moderator' | 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='uq_room_user'),)

class ChatRoomMessage(db.Model):
    __tablename__ = "chat_room_messages"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)
    deleted = db.Column(db.Boolean, default=False)

class ChatAttachment(db.Model):
    __tablename__ = "chat_attachments"
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("chat_room_messages.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)          # nome original
    stored_name = db.Column(db.String(255), nullable=False)       # nome salvo (seguro/único)
    mime_type = db.Column(db.String(100), nullable=False, default="application/pdf")
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
