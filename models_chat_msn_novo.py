from datetime import datetime
from models import db


class ChatMsnRoom(db.Model):
    __tablename__ = "chat_msn_rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    kind = db.Column(db.String(20), nullable=False, default="group")  # 'group' | 'dm'
    created_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # para DM: "dm:<menor_id>:<maior_id>" | para grupo: NULL
    dm_key = db.Column(db.String(64), unique=True, nullable=True)

    members = db.relationship("ChatMsnMember", back_populates="room", cascade="all, delete-orphan")
    messages = db.relationship("ChatMsnMessage", back_populates="room", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "kind": self.kind, 
            "dm_key": self.dm_key,
            "created_by": self.created_by, 
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChatMsnMember(db.Model):
    __tablename__ = "chat_msn_members"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_msn_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # 'owner' | 'admin' | 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    room = db.relationship("ChatMsnRoom", back_populates="members")
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id, 
            "room_id": self.room_id, 
            "user_id": self.user_id,
            "role": self.role, 
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }


class ChatMsnMessage(db.Model):
    __tablename__ = "chat_msn_messages"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("chat_msn_rooms.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(20), default="text", nullable=False)  # text, file, image
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)

    room = db.relationship("ChatMsnRoom", back_populates="messages")
    user = db.relationship("User", foreign_keys=[user_id])
    attachments = db.relationship("ChatMsnAttachment", back_populates="message", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, 
            "room_id": self.room_id, 
            "user_id": self.user_id,
            "content": self.content, 
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deleted": self.deleted,
            "attachments": [att.to_dict() for att in self.attachments]
        }


class ChatMsnAttachment(db.Model):
    __tablename__ = "chat_msn_attachments"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("chat_msn_messages.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    message = db.relationship("ChatMsnMessage", back_populates="attachments")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }
