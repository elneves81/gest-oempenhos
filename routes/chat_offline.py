from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, User
from datetime import datetime
import uuid

# Blueprint para chat offline
chat_offline = Blueprint('chat_offline', __name__, url_prefix='/chat-offline')

# Armazenamento em memória para mensagens (simples para demonstração)
chat_rooms = {}
user_sessions = {}

@chat_offline.route('/')
@login_required
def index():
    """Página principal do chat offline"""
    # Criar sala geral se não existir
    if 'geral' not in chat_rooms:
        chat_rooms['geral'] = {
            'name': 'Chat Geral',
            'messages': [],
            'users': set()
        }
    
    # Adicionar usuário à sala geral
    chat_rooms['geral']['users'].add(current_user.id)
    
    # Buscar usuários online
    online_users = []
    for user_id in chat_rooms['geral']['users']:
        user = User.query.get(user_id)
        if user:
            online_users.append({
                'id': user.id,
                'username': user.username
            })
    
    return render_template('chat_offline/fixed.html', 
                         messages=chat_rooms['geral']['messages'],
                         online_users=online_users,
                         current_room='geral')

@chat_offline.route('/send_message', methods=['POST'])
@login_required
def send_message():
    """Enviar mensagem no chat"""
    data = request.get_json()
    message_text = data.get('message', '').strip()
    room = data.get('room', 'geral')
    
    if not message_text:
        return jsonify({'success': False, 'error': 'Mensagem vazia'}), 400
    
    # Criar sala se não existir
    if room not in chat_rooms:
        chat_rooms[room] = {
            'name': f'Chat {room.title()}',
            'messages': [],
            'users': set()
        }
    
    # Criar mensagem
    message = {
        'id': str(uuid.uuid4()),
        'user_id': current_user.id,
        'username': current_user.username,
        'message': message_text,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'room': room
    }
    
    # Adicionar à sala
    chat_rooms[room]['messages'].append(message)
    chat_rooms[room]['users'].add(current_user.id)
    
    # Manter apenas últimas 100 mensagens por sala
    if len(chat_rooms[room]['messages']) > 100:
        chat_rooms[room]['messages'] = chat_rooms[room]['messages'][-100:]
    
    return jsonify({
        'success': True,
        'message': message
    })

@chat_offline.route('/get_messages')
@login_required
def get_messages():
    """Buscar mensagens recentes"""
    room = request.args.get('room', 'geral')
    
    if room not in chat_rooms:
        return jsonify({'messages': []})
    
    messages = chat_rooms[room]['messages']
    return jsonify({'messages': messages})

@chat_offline.route('/get_users')
@login_required
def get_users():
    """Buscar usuários online"""
    room = request.args.get('room', 'geral')
    
    if room not in chat_rooms:
        return jsonify({'users': []})
    
    online_users = []
    for user_id in chat_rooms[room]['users']:
        user = User.query.get(user_id)
        if user:
            online_users.append({
                'id': user.id,
                'username': user.username,
                'is_current': user.id == current_user.id
            })
    
    return jsonify({'users': online_users})

@chat_offline.route('/leave_room', methods=['POST'])
@login_required
def leave_room():
    """Sair de uma sala"""
    data = request.get_json()
    room = data.get('room', 'geral')
    
    if room in chat_rooms and current_user.id in chat_rooms[room]['users']:
        chat_rooms[room]['users'].discard(current_user.id)
    
    return jsonify({'success': True})

@chat_offline.route('/clear_room', methods=['POST'])
@login_required
def clear_room():
    """Limpar mensagens de uma sala (apenas para admin)"""
    # Verificar se é admin de forma segura
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin:
        return jsonify({'success': False, 'error': 'Apenas administradores podem limpar o chat'}), 403
    
    data = request.get_json()
    room = data.get('room', 'geral')
    
    if room in chat_rooms:
        chat_rooms[room]['messages'] = []
    
    return jsonify({'success': True})
