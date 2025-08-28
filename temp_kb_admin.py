# routes_ai_kb_admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from functools import wraps

ai_kb_admin = Blueprint("ai_kb_admin", __name__, url_prefix="/admin/ai/kb")

def get_db():
    """Obtém a instância do SQLAlchemy da aplicação atual"""
    from flask import current_app
    return current_app.extensions['sqlalchemy']

def admin_required(f):
    @wraps(f)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))  # Corrigido para usar 'login' em vez de 'auth.login'
        # TODO: implementar verificação de admin quando tiver o campo
        # if not current_user.is_admin: 
        #     flash('Acesso negado - apenas administradores', 'danger')
        #     return redirect(url_for('painel'))
        return f(*args, **kwargs)
    return wrapped_view

def _dialect() -> str:
    """Retorna o nome do dialeto em uso: 'mysql', 'sqlite', 'postgresql', etc."""
    db = get_db()
    bind = db.session.get_bind()
    return (bind.dialect.name if bind else "sqlite").lower()

def _bool_to_int(v) -> int:
    return 1 if (v in (True, "1", "on", "true", "True")) else 0

@ai_kb_admin.get("/")
@admin_required
def kb_list():
    """Lista todas as entradas da KB com busca FULLTEXT MySQL"""
    q = (request.args.get("q") or "").strip()
    rows = []
    
    db = get_db()
    
    if q:
        # Busca FULLTEXT MySQL
        sql = """
        SELECT id, question, answer, keywords, is_active,
               MATCH(question, answer, keywords) AGAINST(:q IN NATURAL LANGUAGE MODE) AS score
        FROM ai_kb_entries
        WHERE is_active = 1 AND MATCH(question, answer, keywords) AGAINST(:q IN NATURAL LANGUAGE MODE)
        ORDER BY score DESC LIMIT 100;
        """
        rows = db.session.execute(text(sql), {"q": q}).mappings().all()
    else:
        rows = db.session.execute(text("""
            SELECT id, question, answer, keywords, is_active
            FROM ai_kb_entries ORDER BY updated_at DESC LIMIT 100
        """)).mappings().all()
    
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
        db.session.execute(text("""
            INSERT INTO ai_kb_entries(question, answer, keywords, is_active)
            VALUES (:q, :a, :k, :ia)
        """), {
            "q": f["question"], 
            "a": f["answer"], 
            "k": f.get("keywords", ""), 
            "ia": 1 if f.get("is_active") else 0
        })
        db.session.commit()
        flash("Entrada criada com sucesso!", "success")
        return redirect(url_for("ai_kb_admin.kb_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao criar entrada: {e}", "danger")
        return render_template("ai_kb_form.html", e=None)

@ai_kb_admin.get("/<int:id>/edit")
@admin_required
def kb_edit(id):
    """Formulário para editar entrada"""
    e = db.session.execute(text("SELECT * FROM ai_kb_entries WHERE id=:id"), {"id": id}).mappings().first()
    if not e:
        flash("Entrada não encontrada", "danger")
        return redirect(url_for("ai_kb_admin.kb_list"))
    return render_template("ai_kb_form.html", e=e)

@ai_kb_admin.post("/<int:id>/edit")
@admin_required
def kb_update(id):
    """Atualizar entrada existente"""
    f = request.form
    
    try:
        db.session.execute(text("""
            UPDATE ai_kb_entries
            SET question=:q, answer=:a, keywords=:k, is_active=:ia, updated_at=CURRENT_TIMESTAMP
            WHERE id=:id
        """), {
            "q": f["question"], 
            "a": f["answer"], 
            "k": f.get("keywords", ""), 
            "ia": 1 if f.get("is_active") else 0, 
            "id": id
        })
        db.session.commit()
        flash("Entrada atualizada com sucesso!", "success")
        return redirect(url_for("ai_kb_admin.kb_list"))
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao atualizar entrada: {e}", "danger")
        return redirect(url_for("ai_kb_admin.kb_edit", id=id))

@ai_kb_admin.post("/<int:id>/delete")
@admin_required
def kb_delete(id):
    """Remover entrada da KB"""
    try:
        # Remove links relacionados primeiro
        db.session.execute(text("DELETE FROM ai_kb_links WHERE source_id=:id OR target_id=:id"), {"id": id})
        # Remove a entrada
        db.session.execute(text("DELETE FROM ai_kb_entries WHERE id=:id"), {"id": id})
        db.session.commit()
        flash("Entrada removida com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover entrada: {e}", "danger")
    
    return redirect(url_for("ai_kb_admin.kb_list"))

@ai_kb_admin.post("/link")
@admin_required
def kb_link():
    """Linkar perguntas (relacionar)"""
    data = request.get_json() or request.form
    
    try:
        src = int(data["source_id"])
        tgt = int(data["target_id"])
        rel = data.get("relation", "related")
        
        db.session.execute(text("""
            INSERT OR IGNORE INTO ai_kb_links(source_id, target_id, relation) 
            VALUES (:s, :t, :r)
        """), {"s": src, "t": tgt, "r": rel})
        db.session.commit()
        
        if request.is_json:
            return jsonify({"ok": True})
        else:
            flash("Link criado com sucesso!", "success")
            return redirect(url_for("ai_kb_admin.kb_list"))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({"error": str(e)}), 400
        else:
            flash(f"Erro ao criar link: {e}", "danger")
            return redirect(url_for("ai_kb_admin.kb_list"))

@ai_kb_admin.get("/<int:id>/links")
@admin_required
def kb_links(id):
    """Ver links de uma entrada"""
    entry = db.session.execute(text("SELECT * FROM ai_kb_entries WHERE id=:id"), {"id": id}).mappings().first()
    if not entry:
        flash("Entrada não encontrada", "danger")
        return redirect(url_for("ai_kb_admin.kb_list"))
    
    # Links onde esta entrada é source
    outgoing = db.session.execute(text("""
        SELECT l.*, e.question as target_question
        FROM ai_kb_links l
        JOIN ai_kb_entries e ON e.id = l.target_id
        WHERE l.source_id = :id
    """), {"id": id}).mappings().all()
    
    # Links onde esta entrada é target
    incoming = db.session.execute(text("""
        SELECT l.*, e.question as source_question
        FROM ai_kb_links l
        JOIN ai_kb_entries e ON e.id = l.source_id
        WHERE l.target_id = :id
    """), {"id": id}).mappings().all()
    
    return render_template("ai_kb_links.html", entry=entry, outgoing=outgoing, incoming=incoming)

@ai_kb_admin.get("/stats")
@admin_required
def kb_stats():
    """Estatísticas da KB"""
    stats = {}
    
    # Total de entradas
    stats['total_entries'] = db.session.execute(text("SELECT COUNT(*) as count FROM ai_kb_entries")).scalar()
    stats['active_entries'] = db.session.execute(text("SELECT COUNT(*) as count FROM ai_kb_entries WHERE is_active=1")).scalar()
    stats['total_links'] = db.session.execute(text("SELECT COUNT(*) as count FROM ai_kb_links")).scalar()
    
    # Entradas mais linkadas
    popular = db.session.execute(text("""
        SELECT e.id, e.question, COUNT(l.target_id) as link_count
        FROM ai_kb_entries e
        LEFT JOIN ai_kb_links l ON l.target_id = e.id
        GROUP BY e.id, e.question
        ORDER BY link_count DESC
        LIMIT 10
    """)).mappings().all()
    
    stats['popular_entries'] = popular
    
    return render_template("ai_kb_stats.html", stats=stats)
