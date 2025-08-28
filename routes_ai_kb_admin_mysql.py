#!/usr/bin/env python3
# routes_ai_kb_admin_mysql.py
"""
Blueprint standalone para administração da Base de Conhecimento da IA
Versão MySQL para XAMPP
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do MySQL para XAMPP
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'chat_empenho',
    'user': 'root',
    'password': '',  # XAMPP padrão sem senha
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Criar blueprint
ai_kb_admin = Blueprint('ai_kb_admin', __name__, url_prefix='/admin/ai/kb')

def get_mysql_connection():
    """Conecta ao MySQL"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None

def admin_required(f):
    """Decorator para verificar se o usuário é admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Login necessário.', 'error')
            return redirect(url_for('auth.login'))
        if not getattr(current_user, 'is_admin', False):
            flash('Acesso negado. Apenas administradores.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def init_mysql_tables():
    """Inicializa as tabelas MySQL para a Base de Conhecimento"""
    connection = get_mysql_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Criar tabela ai_kb_entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_kb_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'geral',
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_title (title(255)),
                INDEX idx_category (category),
                INDEX idx_created_at (created_at),
                FULLTEXT(title, content, tags)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Criar tabela ai_kb_links
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_kb_links (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_entry_id INT NOT NULL,
                to_entry_id INT NOT NULL,
                link_type VARCHAR(50) DEFAULT 'related',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_entry_id) REFERENCES ai_kb_entries(id) ON DELETE CASCADE,
                FOREIGN KEY (to_entry_id) REFERENCES ai_kb_entries(id) ON DELETE CASCADE,
                UNIQUE KEY unique_link (from_entry_id, to_entry_id, link_type),
                INDEX idx_from_entry (from_entry_id),
                INDEX idx_to_entry (to_entry_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        logger.info("Tabelas MySQL da Base de Conhecimento criadas com sucesso")
        return True
        
    except Error as e:
        logger.error(f"Erro ao criar tabelas MySQL: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def populate_sample_data():
    """Popula dados de exemplo na Base de Conhecimento"""
    connection = get_mysql_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar se já existem dados
        cursor.execute("SELECT COUNT(*) FROM ai_kb_entries")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logger.info(f"Base de Conhecimento já possui {count} entradas")
            return True
        
        # Dados de exemplo
        sample_entries = [
            {
                'title': 'Sistema de Empenhos - Visão Geral',
                'content': 'O Sistema de Empenhos Municipal é uma aplicação web desenvolvida para gerenciar empenhos, contratos e notas fiscais de órgãos públicos municipais. Principais funcionalidades: gestão de empenhos, contratos, notas fiscais, relatórios e dashboard executivo.',
                'category': 'sistema',
                'tags': 'empenhos, contratos, municipal, gestão'
            },
            {
                'title': 'Como Criar um Novo Empenho',
                'content': 'Para criar um novo empenho: 1) Acesse o menu Empenhos, 2) Clique em "Novo Empenho", 3) Preencha os campos obrigatórios (número, data, valor, fornecedor), 4) Adicione informações do contrato se aplicável, 5) Salve o empenho.',
                'category': 'tutorial',
                'tags': 'empenho, criar, tutorial, passo-a-passo'
            },
            {
                'title': 'Gestão de Contratos',
                'content': 'O sistema permite gerenciar contratos municipais com funcionalidades como: cadastro de contratos, gestão de aditivos, controle de prazos, vinculação com empenhos, anotações e anexos.',
                'category': 'contratos',
                'tags': 'contratos, aditivos, gestão, municipal'
            },
            {
                'title': 'Dashboard Executivo',
                'content': 'O Dashboard Executivo oferece visão consolidada dos dados com gráficos interativos, KPIs principais, filtros por período, exportação de relatórios e widgets personalizáveis.',
                'category': 'dashboard',
                'tags': 'dashboard, relatórios, kpi, gráficos'
            },
            {
                'title': 'Sistema de Chat e Comunicação',
                'content': 'O sistema inclui chat interno para comunicação entre usuários, sistema de mensagens, notificações e integração com workflow de aprovações.',
                'category': 'comunicacao',
                'tags': 'chat, comunicação, mensagens, workflow'
            }
        ]
        
        # Inserir dados de exemplo
        for entry in sample_entries:
            cursor.execute("""
                INSERT INTO ai_kb_entries (title, content, category, tags)
                VALUES (%s, %s, %s, %s)
            """, (entry['title'], entry['content'], entry['category'], entry['tags']))
        
        connection.commit()
        logger.info(f"Inseridas {len(sample_entries)} entradas de exemplo")
        return True
        
    except Error as e:
        logger.error(f"Erro ao popular dados de exemplo: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@ai_kb_admin.route('/')
@login_required
@admin_required
def index():
    """Lista todas as entradas da Base de Conhecimento"""
    connection = get_mysql_connection()
    if not connection:
        flash('Erro de conexão com o banco de dados', 'error')
        return render_template('ai_kb_list.html', entries=[])
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Buscar parâmetros
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        offset = (page - 1) * per_page
        
        # Construir query
        where_conditions = ["is_active = TRUE"]
        params = []
        
        if search:
            where_conditions.append("(MATCH(title, content, tags) AGAINST (%s IN NATURAL LANGUAGE MODE) OR title LIKE %s OR content LIKE %s)")
            params.extend([search, f'%{search}%', f'%{search}%'])
        
        if category:
            where_conditions.append("category = %s")
            params.append(category)
        
        where_clause = " AND ".join(where_conditions)
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) as total FROM ai_kb_entries WHERE {where_clause}", params)
        total = cursor.fetchone()['total']
        
        # Buscar entradas
        cursor.execute(f"""
            SELECT id, title, content, category, tags, created_at, updated_at
            FROM ai_kb_entries 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        entries = cursor.fetchall()
        
        # Buscar categorias para filtro
        cursor.execute("SELECT DISTINCT category FROM ai_kb_entries WHERE is_active = TRUE ORDER BY category")
        categories = [row['category'] for row in cursor.fetchall()]
        
        # Calcular paginação
        total_pages = (total + per_page - 1) // per_page
        
        return render_template('ai_kb_list.html', 
                             entries=entries,
                             categories=categories,
                             search=search,
                             category=category,
                             page=page,
                             total_pages=total_pages,
                             total=total)
        
    except Error as e:
        logger.error(f"Erro ao buscar entradas: {e}")
        flash('Erro ao carregar entradas', 'error')
        return render_template('ai_kb_list.html', entries=[])
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@ai_kb_admin.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_entry():
    """Criar nova entrada"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'geral').strip()
        tags = request.form.get('tags', '').strip()
        
        if not title or not content:
            flash('Título e conteúdo são obrigatórios', 'error')
            return render_template('ai_kb_form.html', 
                                 title=title, content=content, 
                                 category=category, tags=tags)
        
        connection = get_mysql_connection()
        if not connection:
            flash('Erro de conexão com o banco de dados', 'error')
            return render_template('ai_kb_form.html')
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO ai_kb_entries (title, content, category, tags)
                VALUES (%s, %s, %s, %s)
            """, (title, content, category, tags))
            
            connection.commit()
            flash('Entrada criada com sucesso!', 'success')
            return redirect(url_for('ai_kb_admin.index'))
            
        except Error as e:
            logger.error(f"Erro ao criar entrada: {e}")
            flash('Erro ao criar entrada', 'error')
            connection.rollback()
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('ai_kb_form.html')

@ai_kb_admin.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_entry(entry_id):
    """Editar entrada existente"""
    connection = get_mysql_connection()
    if not connection:
        flash('Erro de conexão com o banco de dados', 'error')
        return redirect(url_for('ai_kb_admin.index'))
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            category = request.form.get('category', 'geral').strip()
            tags = request.form.get('tags', '').strip()
            
            if not title or not content:
                flash('Título e conteúdo são obrigatórios', 'error')
                return render_template('ai_kb_form.html', 
                                     entry_id=entry_id, title=title, 
                                     content=content, category=category, tags=tags)
            
            cursor.execute("""
                UPDATE ai_kb_entries 
                SET title = %s, content = %s, category = %s, tags = %s
                WHERE id = %s
            """, (title, content, category, tags, entry_id))
            
            connection.commit()
            flash('Entrada atualizada com sucesso!', 'success')
            return redirect(url_for('ai_kb_admin.index'))
        
        # GET - carregar dados da entrada
        cursor.execute("SELECT * FROM ai_kb_entries WHERE id = %s", (entry_id,))
        entry = cursor.fetchone()
        
        if not entry:
            flash('Entrada não encontrada', 'error')
            return redirect(url_for('ai_kb_admin.index'))
        
        return render_template('ai_kb_form.html', entry=entry)
        
    except Error as e:
        logger.error(f"Erro ao editar entrada: {e}")
        flash('Erro ao editar entrada', 'error')
        return redirect(url_for('ai_kb_admin.index'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@ai_kb_admin.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_entry(entry_id):
    """Deletar entrada"""
    connection = get_mysql_connection()
    if not connection:
        flash('Erro de conexão com o banco de dados', 'error')
        return redirect(url_for('ai_kb_admin.index'))
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE ai_kb_entries SET is_active = FALSE WHERE id = %s", (entry_id,))
        connection.commit()
        flash('Entrada removida com sucesso!', 'success')
        
    except Error as e:
        logger.error(f"Erro ao deletar entrada: {e}")
        flash('Erro ao remover entrada', 'error')
        connection.rollback()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('ai_kb_admin.index'))

@ai_kb_admin.route('/stats')
@login_required
@admin_required
def stats():
    """Estatísticas da Base de Conhecimento"""
    connection = get_mysql_connection()
    if not connection:
        flash('Erro de conexão com o banco de dados', 'error')
        return render_template('ai_kb_stats.html', stats={})
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Estatísticas básicas
        cursor.execute("SELECT COUNT(*) as total FROM ai_kb_entries WHERE is_active = TRUE")
        total_entries = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT category) as total FROM ai_kb_entries WHERE is_active = TRUE")
        total_categories = cursor.fetchone()['total']
        
        # Entradas por categoria
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM ai_kb_entries 
            WHERE is_active = TRUE 
            GROUP BY category 
            ORDER BY count DESC
        """)
        by_category = cursor.fetchall()
        
        # Entradas recentes
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM ai_kb_entries 
            WHERE is_active = TRUE AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 30
        """)
        recent_entries = cursor.fetchall()
        
        stats = {
            'total_entries': total_entries,
            'total_categories': total_categories,
            'by_category': by_category,
            'recent_entries': recent_entries
        }
        
        return render_template('ai_kb_stats.html', stats=stats)
        
    except Error as e:
        logger.error(f"Erro ao carregar estatísticas: {e}")
        flash('Erro ao carregar estatísticas', 'error')
        return render_template('ai_kb_stats.html', stats={})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@ai_kb_admin.route('/search')
@login_required
@admin_required
def search():
    """API de busca para a Base de Conhecimento"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'results': []})
    
    connection = get_mysql_connection()
    if not connection:
        return jsonify({'error': 'Erro de conexão'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, title, content, category, tags,
                   MATCH(title, content, tags) AGAINST (%s IN NATURAL LANGUAGE MODE) as relevance
            FROM ai_kb_entries 
            WHERE is_active = TRUE 
            AND (MATCH(title, content, tags) AGAINST (%s IN NATURAL LANGUAGE MODE)
                 OR title LIKE %s OR content LIKE %s)
            ORDER BY relevance DESC, created_at DESC
            LIMIT 10
        """, (query, query, f'%{query}%', f'%{query}%'))
        
        results = cursor.fetchall()
        
        # Truncar conteúdo para preview
        for result in results:
            if len(result['content']) > 200:
                result['content'] = result['content'][:200] + '...'
        
        return jsonify({'results': results})
        
    except Error as e:
        logger.error(f"Erro na busca: {e}")
        return jsonify({'error': 'Erro na busca'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@ai_kb_admin.route('/test')
@login_required
@admin_required
def test():
    """Página de teste da Base de Conhecimento"""
    # Testar conexão
    connection = get_mysql_connection()
    if not connection:
        return jsonify({
            'status': 'error',
            'message': 'Erro de conexão com MySQL',
            'mysql_config': MYSQL_CONFIG
        })
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Testar tabelas
        cursor.execute("SHOW TABLES LIKE 'ai_kb_%'")
        tables = cursor.fetchall()
        
        # Contar entradas
        cursor.execute("SELECT COUNT(*) as count FROM ai_kb_entries")
        entry_count = cursor.fetchone()['count']
        
        return jsonify({
            'status': 'success',
            'message': 'Base de Conhecimento MySQL funcionando!',
            'tables': [list(table.values())[0] for table in tables],
            'entry_count': entry_count,
            'mysql_config': {k: v if k != 'password' else '***' for k, v in MYSQL_CONFIG.items()}
        })
        
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro no teste: {str(e)}',
            'mysql_config': {k: v if k != 'password' else '***' for k, v in MYSQL_CONFIG.items()}
        })
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Inicializar tabelas quando o blueprint for importado
try:
    if init_mysql_tables():
        populate_sample_data()
        logger.info("Base de Conhecimento MySQL inicializada com sucesso")
    else:
        logger.error("Falha ao inicializar Base de Conhecimento MySQL")
except Exception as e:
    logger.error(f"Erro na inicialização: {e}")
