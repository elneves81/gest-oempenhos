# routes_ai_kb_api.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db
from sqlalchemy import text

ai_kb_api = Blueprint("ai_kb_api", __name__, url_prefix="/api/ai/kb")

@ai_kb_api.get("/search")
def kb_search():
    """API para buscar na KB - usada pelo chat"""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": []})
    
    try:
        sql = """
        SELECT e.id, e.question, e.answer, e.keywords,
               bm25(ai_kb_entries_fts) AS score,
               snippet(ai_kb_entries_fts, 0, '<mark>', '</mark>', '...', 32) as question_snippet,
               snippet(ai_kb_entries_fts, 1, '<mark>', '</mark>', '...', 64) as answer_snippet
        FROM ai_kb_entries_fts f
        JOIN ai_kb_entries e ON e.id = f.rowid
        WHERE e.is_active = 1 AND ai_kb_entries_fts MATCH :q
        ORDER BY score ASC
        LIMIT 5;
        """
        rows = db.session.execute(text(sql), {"q": q}).mappings().all()
        results = []
        
        for row in rows:
            result = dict(row)
            # Buscar links relacionados
            related = db.session.execute(text("""
                SELECT e2.id, e2.question, l.relation
                FROM ai_kb_links l
                JOIN ai_kb_entries e2 ON e2.id = l.target_id
                WHERE l.source_id = :id AND e2.is_active = 1
                LIMIT 3
            """), {"id": row.id}).mappings().all()
            
            result['related'] = [dict(r) for r in related]
            results.append(result)
        
        return jsonify({"results": results})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_kb_api.post("/")
@login_required
def kb_create_api():
    """API para criar entrada na KB - usada pelo chat"""
    j = request.get_json() or {}
    q = (j.get("question") or "").strip()
    a = (j.get("answer") or "").strip()
    k = (j.get("keywords") or "").strip()
    
    if not q or not a:
        return jsonify({"error": "question e answer são obrigatórios"}), 400
    
    try:
        result = db.session.execute(text("""
            INSERT INTO ai_kb_entries(question, answer, keywords, is_active)
            VALUES (:q, :a, :k, 1)
            RETURNING id
        """), {"q": q, "a": a, "k": k})
        
        new_id = result.scalar()
        db.session.commit()
        
        return jsonify({"ok": True, "id": new_id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@ai_kb_api.post("/link")
@login_required
def kb_link_api():
    """API para linkar entradas"""
    j = request.get_json() or {}
    
    try:
        src = int(j["source_id"])
        tgt = int(j["target_id"])
        rel = j.get("relation", "related")
        
        db.session.execute(text("""
            INSERT OR IGNORE INTO ai_kb_links(source_id, target_id, relation) 
            VALUES (:s, :t, :r)
        """), {"s": src, "t": tgt, "r": rel})
        db.session.commit()
        
        return jsonify({"ok": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@ai_kb_api.get("/suggest")
def kb_suggest():
    """Sugerir entradas similares para linkagem"""
    q = (request.args.get("q") or "").strip()
    exclude_id = request.args.get("exclude_id", type=int)
    
    if not q:
        return jsonify({"suggestions": []})
    
    try:
        sql = """
        SELECT e.id, e.question, e.keywords,
               bm25(ai_kb_entries_fts) AS score
        FROM ai_kb_entries_fts f
        JOIN ai_kb_entries e ON e.id = f.rowid
        WHERE e.is_active = 1 AND ai_kb_entries_fts MATCH :q
        """
        
        params = {"q": q}
        if exclude_id:
            sql += " AND e.id != :exclude_id"
            params["exclude_id"] = exclude_id
            
        sql += " ORDER BY score ASC LIMIT 10"
        
        rows = db.session.execute(text(sql), params).mappings().all()
        suggestions = [dict(r) for r in rows]
        
        return jsonify({"suggestions": suggestions})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_kb_api.get("/popular")
def kb_popular():
    """Entradas mais populares/linkadas"""
    try:
        sql = """
        SELECT e.id, e.question, e.keywords, COUNT(l.target_id) as link_count
        FROM ai_kb_entries e
        LEFT JOIN ai_kb_links l ON l.target_id = e.id
        WHERE e.is_active = 1
        GROUP BY e.id, e.question, e.keywords
        ORDER BY link_count DESC, e.updated_at DESC
        LIMIT 10
        """
        
        rows = db.session.execute(text(sql)).mappings().all()
        popular = [dict(r) for r in rows]
        
        return jsonify({"popular": popular})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Função helper para usar no chat
def kb_best_match(pergunta: str):
    """Encontra a melhor resposta na KB para uma pergunta"""
    # 1) Tenta FTS por pergunta inteira
    sql = """
    SELECT e.id, e.question, e.answer, e.keywords, bm25(ai_kb_entries_fts) AS score
    FROM ai_kb_entries_fts f
    JOIN ai_kb_entries e ON e.id = f.rowid
    WHERE e.is_active=1 AND ai_kb_entries_fts MATCH :q
    ORDER BY score ASC LIMIT 1;
    """
    row = db.session.execute(text(sql), {"q": pergunta}).mappings().first()
    if row: 
        return dict(row)

    # 2) Reforço: usa palavras-chave separadas (OR)
    terms = [t for t in pergunta.split() if len(t) >= 3]
    if not terms: 
        return None
        
    q = " OR ".join(terms)
    row = db.session.execute(text(sql), {"q": q}).mappings().first()
    return dict(row) if row else None

def responder_kb(pergunta: str):
    """Responde usando a KB ou indica que não tem resposta"""
    hit = kb_best_match(pergunta)
    if hit:
        # Buscar entradas relacionadas
        related = db.session.execute(text("""
            SELECT e2.id, e2.question, l.relation
            FROM ai_kb_links l
            JOIN ai_kb_entries e2 ON e2.id = l.target_id
            WHERE l.source_id = :id AND e2.is_active = 1
            LIMIT 3
        """), {"id": hit["id"]}).mappings().all()
        
        return hit["answer"], {
            "kb_id": hit["id"], 
            "matched_question": hit["question"],
            "score": hit["score"],
            "related": [dict(r) for r in related]
        }
    
    # Fallback: não encontrou na KB
    return None, {"suggestion": "Quer cadastrar esta pergunta na base de conhecimento?"}
