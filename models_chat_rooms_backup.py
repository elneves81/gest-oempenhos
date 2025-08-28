from datetime import datetime
from models import db
from sqlalchemy import UniqueConstraint


class ChatRoom(db.Model):
    __tablename__ = "chat_rooms"
    __table_args__ = {"extend_existing": True}

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    kind       = db.Column(db.String(20), nullable=False, default="group", index=True)  # 'group' | 'dm'
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # para DM: "dm:<menor_id>:<maior_id>" | para grupo: NULL
    dm_key     = db.Column(db.String(64), unique=True, nullable=True)

    creator  = db.relationship("User", foreign_keys=[created_by])
    members  = db.relationship("ChatMember", back_populates="room", cascade="all, delete-orphan")
    messages = db.relationship("ChatRoomMessage", back_populates="room", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "kind": self.kind, "dm_key": self.dm_key,
            "created_by": self.created_by, "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChatMember(db.Model):
    __tablename__ = "chat_members"
    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_room_user"),
        {"extend_existing": True},
    )

    id       = db.Column(db.Integer, primary_key=True)
    room_id  = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role     = db.Column(db.String(20), nullable=False, default="member")  # 'owner' | 'admin' | 'member'
    joined_at= db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    room = db.relationship("ChatRoom", back_populates="members")
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id, "room_id": self.room_id, "user_id": self.user_id,
            "role": self.role, "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }


class ChatRoomMessage(db.Model):
    __tablename__ = "chat_room_messages"
    __table_args__ = {"extend_existing": True}

    id        = db.Column(db.Integer, primary_key=True)
    room_id   = db.Column(db.Integer, db.ForeignKey("chat_rooms.id"), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # use sempre 'content'; 'text' fica como legado (pode existir em DB antigo)
    content   = db.Column(db.Text, nullable=True)
    text      = db.Column(db.Text, nullable=True)      # legado
    created_at= db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deleted   = db.Column(db.Boolean, default=False, nullable=False)

    room = db.relationship("ChatRoom", back_populates="messages")
    user = db.relationship("User", foreign_keys=[user_id])

    @property
    def body(self):
        return self.content or self.text or ""

    def to_dict(self):
        return {
            "id": self.id, "room_id": self.room_id, "user_id": self.user_id,
            "content": self.body, "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted": self.deleted
        }


class ChatRoomMessage(db.Model):
    __tablename__ = 'chat_room_messages'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Campo principal para mensagens
    text = db.Column(db.Text, nullable=True)      # Campo alternativo para compatibilidade
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)

    room = db.relationship('ChatRoom', back_populates='messages')
    user = db.relationship('User', backref='chat_room_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'content': self.content or self.text or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'deleted': self.deleted
        }
