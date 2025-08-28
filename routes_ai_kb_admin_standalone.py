# routes_ai_kb_admin_standalone.py
"""
Blueprint AI KB Admin - Versão Standalone
Funciona independentemente do SQLAlchemy problemático
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
import os
from functools import wraps

ai_kb_admin = Blueprint("ai_kb_admin", __name__, url_prefix="/admin/ai/kb")

# Caminho do banco de dados
DB_PATH = "empenhos.db"

def admin_required(f):
    @wraps(f)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # TODO: implementar verificação de admin quando tiver o campo
        # if not current_user.is_admin: 
        #     flash('Acesso negado - apenas administradores', 'danger')
        #     return redirect(url_for('painel'))
        return f(*args, **kwargs)
    return wrapped_view

def get_db_connection():
    """Obter conexão com o banco de dados"""
    if not os.path.exists(DB_PATH):
        raise Exception(f"Banco de dados não encontrado: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

@ai_kb_admin.get("/")
@admin_required
def kb_list():
    """Lista todas as entradas da KB com busca FTS5"""
    q = (request.args.get("q") or "").strip()
    rows = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if q:
            # Busca FTS5 (usa bm25 p/ ordenar)
            cursor.execute("""
            SELECT e.id, e.question, e.answer, e.keywords, e.is_active,
                   bm25(ai_kb_entries_fts) AS score
            FROM ai_kb_entries_fts f
            JOIN ai_kb_entries e ON e.id = f.rowid
            WHERE ai_kb_entries_fts MATCH ?
            ORDER BY score ASC LIMIT 100
            """, (q,))
        else:
            cursor.execute("""
            SELECT id, question, answer, keywords, is_active
            FROM ai_kb_entries ORDER BY updated_at DESC LIMIT 100
            """)
        
        rows = [dict(zip([col[0] for col in cursor.description], row)) 
                for row in cursor.fetchall()]
        
        conn.close()
        
    except Exception as e:
        flash(f"Erro ao buscar entradas: {e}", "danger")
        rows = []
    
    return render_template("ai_kb_list.html", rows=rows, q=q)

@ai_kb_admin.get("/new")
@admin_required
def kb_new():
    """Formulário para nova entrada"""
    return render_template("ai_kb_form.html", e=None)

@ai_kb_admin.post("/new")
@admin_required
def kb_create():
    """Criar nova entrada na KB"""
    f = request.form
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO ai_kb_entries(question, answer, keywords, is_active)
        VALUES (?, ?, ?, ?)
        """, (
            f["question"], 
            f["answer"], 
            f.get("keywords", ""), 
            1 if f.get("is_active") else 0
        ))
        
        conn.commit()
        conn.close()
        
        flash("Entrada criada com sucesso!", "success")
        return redirect(url_for("ai_kb_admin.kb_list"))
        
    except Exception as e:
        flash(f"Erro ao criar entrada: {e}", "danger")
        return render_template("ai_kb_form.html", e=None)

@ai_kb_admin.get("/<int:id>/edit")
@admin_required
def kb_edit(id):
    """Formulário para editar entrada"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ai_kb_entries WHERE id=?", (id,))
        row = cursor.fetchone()
        
        if not row:
            flash("Entrada não encontrada", "danger")
            return redirect(url_for("ai_kb_admin.kb_list"))
        
        # Converter para dict
        e = dict(zip([col[0] for col in cursor.description], row))
        conn.close()
        
        return render_template("ai_kb_form.html", e=e)
        
    except Exception as e:
        flash(f"Erro ao buscar entrada: {e}", "danger")
        return redirect(url_for("ai_kb_admin.kb_list"))

@ai_kb_admin.post("/<int:id>/edit")
@admin_required
def kb_update(id):
    """Atualizar entrada existente"""
    f = request.form
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE ai_kb_entries
        SET question=?, answer=?, keywords=?, is_active=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """, (
            f["question"], 
            f["answer"], 
            f.get("keywords", ""), 
            1 if f.get("is_active") else 0, 
            id
        ))
        
        conn.commit()
        conn.close()
        
        flash("Entrada atualizada com sucesso!", "success")
        return redirect(url_for("ai_kb_admin.kb_list"))
        
    except Exception as e:
        flash(f"Erro ao atualizar entrada: {e}", "danger")
        return redirect(url_for("ai_kb_admin.kb_edit", id=id))

@ai_kb_admin.post("/<int:id>/delete")
@admin_required
def kb_delete(id):
    """Remover entrada da KB"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Remove links relacionados primeiro
        cursor.execute("DELETE FROM ai_kb_links WHERE source_id=? OR target_id=?", (id, id))
        # Remove a entrada
        cursor.execute("DELETE FROM ai_kb_entries WHERE id=?", (id,))
        
        conn.commit()
        conn.close()
        
        flash("Entrada removida com sucesso!", "success")
        
    except Exception as e:
        flash(f"Erro ao remover entrada: {e}", "danger")
    
    return redirect(url_for("ai_kb_admin.kb_list"))

@ai_kb_admin.get("/stats")
@admin_required
def kb_stats():
    """Estatísticas da KB"""
    stats = {}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de entradas
        cursor.execute("SELECT COUNT(*) FROM ai_kb_entries")
        stats['total_entries'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_kb_entries WHERE is_active=1")
        stats['active_entries'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_kb_links")
        stats['total_links'] = cursor.fetchone()[0]
        
        # Entradas mais linkadas
        cursor.execute("""
        SELECT e.id, e.question, COUNT(l.target_id) as link_count
        FROM ai_kb_entries e
        LEFT JOIN ai_kb_links l ON l.target_id = e.id
        GROUP BY e.id, e.question
        ORDER BY link_count DESC
        LIMIT 10
        """)
        
        popular = [dict(zip([col[0] for col in cursor.description], row)) 
                  for row in cursor.fetchall()]
        
        stats['popular_entries'] = popular
        conn.close()
        
    except Exception as e:
        flash(f"Erro ao obter estatísticas: {e}", "danger")
        stats = {
            'total_entries': 0,
            'active_entries': 0,
            'total_links': 0,
            'popular_entries': []
        }
    
    return render_template("ai_kb_stats.html", stats=stats)

# Rota de teste para verificar se está funcionando
@ai_kb_admin.get("/test")
@admin_required
def kb_test():
    """Rota de teste"""
    return jsonify({
        'status': 'OK',
        'message': 'Blueprint AI KB Admin está funcionando!',
        'blueprint': ai_kb_admin.name,
        'url_prefix': ai_kb_admin.url_prefix
    })
