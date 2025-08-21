# chat_ai_kb.py
"""
Integração do Chat com a Base de Conhecimento
Funções para buscar respostas na KB e melhorar o chat IA
"""

from routes_ai_kb_api import kb_best_match, responder_kb
from models import db
from sqlalchemy import text

def chat_with_kb(pergunta: str, user_id: int = None):
    """
    Processa uma pergunta do chat integrando com a Base de Conhecimento
    
    Args:
        pergunta: Pergunta do usuário
        user_id: ID do usuário (para logs/analytics)
    
    Returns:
        dict: {
            'answer': str,          # Resposta final
            'source': str,          # 'kb' ou 'fallback'
            'kb_match': dict,       # Dados da KB se encontrou
            'suggestions': list,    # Sugestões de perguntas relacionadas
            'should_save': bool     # Se deve oferecer salvar na KB
        }
    """
    
    # 1. Tentar buscar na KB primeiro
    try:
        answer, meta = responder_kb(pergunta)
        
        if answer and 'kb_id' in meta:
            # Encontrou resposta na KB
            return {
                'answer': answer,
                'source': 'kb',
                'kb_match': meta,
                'suggestions': meta.get('related', []),
                'should_save': False,
                'confidence': 'high'
            }
            
    except Exception as e:
        print(f"Erro ao consultar KB: {e}")
    
    # 2. Fallback para respostas básicas do sistema
    answer = generate_fallback_answer(pergunta)
    
    # 3. Buscar sugestões similares na KB
    suggestions = get_kb_suggestions(pergunta)
    
    return {
        'answer': answer,
        'source': 'fallback',
        'kb_match': None,
        'suggestions': suggestions,
        'should_save': True,  # Oferecer salvar esta resposta
        'confidence': 'medium'
    }

def generate_fallback_answer(pergunta: str):
    """Gera respostas básicas para perguntas comuns do sistema"""
    
    pergunta_lower = pergunta.lower()
    
    # Respostas específicas do sistema de empenhos
    if any(word in pergunta_lower for word in ['empenho', 'empenhos']):
        if any(word in pergunta_lower for word in ['criar', 'novo', 'adicionar']):
            return "Para criar um novo empenho, acesse o menu 'Empenhos' → 'Novo Empenho' e preencha os campos obrigatórios."
        elif any(word in pergunta_lower for word in ['consultar', 'buscar', 'ver']):
            return "Você pode consultar empenhos no menu 'Empenhos'. Use os filtros para encontrar o que precisa."
        elif any(word in pergunta_lower for word in ['status', 'situação']):
            return "Os status de empenhos são: PENDENTE (aguardando), APROVADO (liberado), PAGO (finalizado), REJEITADO (negado)."
    
    elif any(word in pergunta_lower for word in ['contrato', 'contratos']):
        if any(word in pergunta_lower for word in ['criar', 'novo', 'adicionar']):
            return "Para criar um contrato, vá em 'Contratos' → 'Novo Contrato' e preencha as informações necessárias."
        elif any(word in pergunta_lower for word in ['consultar', 'buscar', 'ver']):
            return "Acesse o menu 'Contratos' para ver todos os contratos. Você pode filtrar por status, fornecedor ou período."
    
    elif any(word in pergunta_lower for word in ['relatório', 'relatorios', 'dashboard']):
        return "No menu 'Relatórios' você encontra diversas opções de relatórios e dashboards. Também pode usar o 'Painel Principal' para widgets personalizáveis."
    
    elif any(word in pergunta_lower for word in ['usuário', 'usuarios', 'login', 'senha']):
        return "Para gerenciar usuários, acesse o menu 'Usuários' (apenas administradores). Para alterar sua senha, clique no seu perfil."
    
    elif any(word in pergunta_lower for word in ['ajuda', 'help', 'como usar']):
        return "Este sistema gerencia empenhos e contratos municipais. Use o menu lateral para navegar. Para ajuda específica, descreva o que precisa fazer."
    
    # Resposta genérica
    return "Não tenho uma resposta específica para essa pergunta ainda. Você pode me ajudar adicionando essa informação à base de conhecimento?"

def get_kb_suggestions(pergunta: str, limit: int = 3):
    """Busca sugestões de perguntas similares na KB"""
    
    try:
        # Extrair palavras-chave da pergunta
        words = [w for w in pergunta.split() if len(w) >= 3]
        if not words:
            return []
        
        # Buscar entradas similares
        query_terms = " OR ".join(words[:5])  # Limitar a 5 palavras
        
        sql = """
        SELECT e.id, e.question, e.keywords,
               bm25(ai_kb_entries_fts) AS score
        FROM ai_kb_entries_fts f
        JOIN ai_kb_entries e ON e.id = f.rowid
        WHERE e.is_active = 1 AND ai_kb_entries_fts MATCH :q
        ORDER BY score ASC
        LIMIT :limit
        """
        
        rows = db.session.execute(text(sql), {
            "q": query_terms, 
            "limit": limit
        }).mappings().all()
        
        return [dict(r) for r in rows]
        
    except Exception as e:
        print(f"Erro ao buscar sugestões KB: {e}")
        return []

def save_chat_to_kb(pergunta: str, resposta: str, keywords: str = "", user_id: int = None):
    """
    Salva uma interação do chat na Base de Conhecimento
    
    Args:
        pergunta: Pergunta do usuário
        resposta: Resposta aprovada
        keywords: Palavras-chave (opcional)
        user_id: ID do usuário que salvou
    
    Returns:
        dict: Resultado da operação
    """
    
    try:
        # Extrair palavras-chave automaticamente se não fornecidas
        if not keywords:
            words = pergunta.lower().split()
            # Pegar palavras importantes (> 3 caracteres, não comuns)
            stop_words = {'como', 'para', 'que', 'onde', 'quando', 'porque', 'qual', 'quais'}
            keywords = ", ".join([w for w in words if len(w) > 3 and w not in stop_words][:5])
        
        # Inserir na KB
        db.session.execute(text("""
            INSERT INTO ai_kb_entries(question, answer, keywords, is_active)
            VALUES (:q, :a, :k, 1)
        """), {
            "q": pergunta.strip(),
            "a": resposta.strip(),
            "k": keywords.strip()
        })
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Pergunta salva na base de conhecimento!'
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'Erro ao salvar na KB: {str(e)}'
        }

def get_kb_stats():
    """Retorna estatísticas rápidas da KB para o chat"""
    
    try:
        stats = {}
        stats['total'] = db.session.execute(text("SELECT COUNT(*) FROM ai_kb_entries")).scalar()
        stats['active'] = db.session.execute(text("SELECT COUNT(*) FROM ai_kb_entries WHERE is_active=1")).scalar()
        stats['links'] = db.session.execute(text("SELECT COUNT(*) FROM ai_kb_links")).scalar()
        
        return stats
        
    except Exception as e:
        print(f"Erro ao obter stats KB: {e}")
        return {'total': 0, 'active': 0, 'links': 0}

# Exemplo de uso no chat:
"""
def processar_mensagem_chat(mensagem, user_id):
    # Usar a KB integrada
    resultado = chat_with_kb(mensagem, user_id)
    
    resposta = {
        'text': resultado['answer'],
        'source': resultado['source'],
        'confidence': resultado['confidence']
    }
    
    # Adicionar sugestões se houver
    if resultado['suggestions']:
        resposta['suggestions'] = [
            f"Você também pode perguntar: {s['question']}"
            for s in resultado['suggestions'][:2]
        ]
    
    # Adicionar opção de salvar se for fallback
    if resultado['should_save']:
        resposta['save_option'] = {
            'message': 'Esta resposta foi útil? Quer salvá-la na base de conhecimento?',
            'action': 'save_to_kb'
        }
    
    return resposta
"""
