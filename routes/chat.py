from flask import Blueprint, render_template, request, jsonify, flash, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, text
from models_chat import ChatMessage, ChatSession
from models import db
import uuid
import os

# OpenAI opcional
OPENAI_AVAILABLE = False
try:
    import openai
    if os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

chat = Blueprint('chat', __name__, url_prefix='/chat')

# ----------------------
# Views / Pages
# ----------------------
@chat.route('/')
@login_required
def index():
    try:
        # Minhas sessões
        sessions = (ChatSession.query
                    .filter_by(user_id=current_user.id)
                    .order_by(ChatSession.last_message_at.desc())
                    .all())

        # Carrega sessão atual (se houver)
        session_id = request.args.get('session_id')
        messages = []
        if session_id:
            messages = (ChatMessage.query
                        .filter_by(session_id=session_id)
                        .order_by(ChatMessage.timestamp.asc())
                        .all())

        return render_template('chat/index.html',
                               sessions=sessions,
                               messages=messages,
                               current_session_id=session_id)
    except Exception as e:
        flash(f'Erro ao carregar chat: {e}', 'error')
        return render_template('chat/index.html', sessions=[], messages=[], current_session_id=None)

# ----------------------
# API: Sessão
# ----------------------
@chat.route('/new_session', methods=['POST'])
@login_required
def new_session():
    try:
        sid = str(uuid.uuid4())
        s = ChatSession(session_id=sid, user_id=current_user.id, title='Nova Conversa')
        db.session.add(s)
        db.session.commit()
        return jsonify(success=True, session_id=sid, redirect_url=url_for('chat.index', session_id=sid))
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500

@chat.route('/delete_session/<session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    try:
        session_obj = ChatSession.query.filter_by(user_id=current_user.id, session_id=session_id).first()
        if not session_obj:
            return jsonify(success=False, error="Sessão não encontrada"), 404
        ChatMessage.query.filter_by(session_id=session_id).delete()
        db.session.delete(session_obj)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500

@chat.route('/get_messages/<session_id>')
@login_required
def get_messages(session_id):
    try:
        s = ChatSession.query.filter_by(user_id=current_user.id, session_id=session_id).first()
        if not s:
            return jsonify(success=False, error="Sessão não encontrada"), 404
        msgs = (ChatMessage.query
                .filter_by(session_id=session_id)
                .order_by(ChatMessage.timestamp.asc())
                .all())
        return jsonify(success=True, messages=[m.to_dict() for m in msgs])
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

# ----------------------
# API: Mensagens
# ----------------------
@chat.route('/ask', methods=['POST'])
@login_required
def ask():
    """
    API dedicada para perguntas diretas ao chat.
    Formato: {"question": "texto da pergunta"}
    Retorna: {"answer": "resposta", "kb_id": id ou null, "matched_question": "pergunta original" ou null}
    """
    try:
        data = request.get_json(force=True) or {}
        question = (data.get('question') or '').strip()
        
        if not question:
            return jsonify({"answer": "Digite uma pergunta.", "kb_id": None, "matched_question": None})
        
        # 🔎 1º tenta no KB
        kb_match = kb_best_match(question)
        if kb_match:
            return jsonify({
                "answer": kb_match["answer"],
                "kb_id": kb_match["id"],
                "matched_question": kb_match["question"]
            })
        
        # 🤖 2º tenta OpenAI 
        if OPENAI_AVAILABLE:
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Você é um assistente para gestão municipal (empenhos/contratos). Seja claro e útil."},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                    timeout=20
                )
                return jsonify({
                    "answer": resp.choices[0].message["content"],
                    "kb_id": None,
                    "matched_question": None
                })
            except Exception:
                pass
        
        # ❌ fallback se não achou
        return jsonify({
            "answer": generate_mock_response(question),
            "kb_id": None,
            "matched_question": None
        })
        
    except Exception as e:
        return jsonify({
            "answer": f"Erro interno: {str(e)}",
            "kb_id": None,
            "matched_question": None
        }), 500

@chat.route('/test_kb', methods=['POST', 'GET'])
def test_kb():
    """
    Rota de teste para verificar integração do KB (sem login)
    """
    if request.method == 'GET':
        return jsonify({"message": "Use POST com {\"question\": \"sua pergunta\"}"})
    
    try:
        data = request.get_json(force=True) or {}
        question = (data.get('question') or '').strip()
        
        if not question:
            return jsonify({"answer": "Digite uma pergunta.", "kb_id": None, "matched_question": None})
        
        # 🔎 Busca no KB
        kb_match = kb_best_match(question)
        if kb_match:
            return jsonify({
                "answer": kb_match["answer"],
                "kb_id": kb_match["id"],
                "matched_question": kb_match["question"],
                "source": "KB"
            })
        
        # ❌ fallback
        return jsonify({
            "answer": generate_mock_response(question),
            "kb_id": None,
            "matched_question": None,
            "source": "MOCK"
        })
        
    except Exception as e:
        return jsonify({
            "answer": f"Erro interno: {str(e)}",
            "kb_id": None,
            "matched_question": None,
            "source": "ERROR"
        }), 500

@chat.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json(force=True) or {}
        text = (data.get('message') or '').strip()
        sid = data.get('session_id')

        if not text:
            return jsonify(success=False, error="Mensagem vazia"), 400
        if not sid:
            return jsonify(success=False, error="Sessão inválida"), 400

        sess = ChatSession.query.filter_by(user_id=current_user.id, session_id=sid).first()
        if not sess:
            return jsonify(success=False, error="Sessão não encontrada"), 404

        # Resposta da IA (ou mock)
        answer = _generate_ai_response(text)

        # Persistir
        msg = ChatMessage(
            user_id=current_user.id,
            message=text,
            response=answer,
            session_id=sid
        )
        db.session.add(msg)

        # Atualizar sessão (título só se for "Nova Conversa")
        sess.last_message_at = datetime.utcnow()
        if sess.title == 'Nova Conversa':
            sess.title = (text[:50] + '…') if len(text) > 50 else text

        db.session.commit()

        return jsonify(success=True, message={
            'id': msg.id,
            'user_message': text,
            'ai_response': answer,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500

# ----------------------
# API: Estatísticas para gráfico
# ----------------------
@chat.route('/stats/messages_per_day')
@login_required
def messages_per_day():
    """
    Retorna { labels: [...], values: [...] } com a quantidade de mensagens do usuário por dia (últimos 14 dias).
    Gráfico funciona mesmo sem IA.
    """
    try:
        # Janela de 14 dias
        start = (datetime.utcnow() - timedelta(days=13)).date()
        end = datetime.utcnow().date()

        # Agrupar por dia (compatível com SQLite e outros usando DATE(timestamp))
        rows = (db.session.query(
                    func.date(ChatMessage.timestamp).label('dia'),
                    func.count(ChatMessage.id).label('qtd')
                )
                .filter(ChatMessage.user_id == current_user.id)
                .filter(func.date(ChatMessage.timestamp) >= start)
                .filter(func.date(ChatMessage.timestamp) <= end)
                .group_by(func.date(ChatMessage.timestamp))
                .order_by(func.date(ChatMessage.timestamp))
                .all())

        # Montar mapa dia -> qtd
        mapa = {str(r.dia): r.qtd for r in rows}

        labels = []
        values = []
        cursor = start
        while cursor <= end:
            ds = cursor.isoformat()
            labels.append(cursor.strftime('%d/%m'))
            values.append(int(mapa.get(ds, 0)))
            cursor += timedelta(days=1)

        return jsonify(success=True, labels=labels, values=values)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

# ----------------------
# Knowledge Base Integration
# ----------------------
def kb_best_match(pergunta: str):
    """
    Busca a melhor correspondência no Knowledge Base usando FTS5.
    Retorna dict com id, question, answer, score ou None se não encontrar.
    """
    try:
        sql = """
        SELECT e.id, e.question, e.answer, bm25(ai_kb_entries_fts) AS score
        FROM ai_kb_entries_fts f
        JOIN ai_kb_entries e ON e.id = f.rowid
        WHERE e.is_active=1 AND ai_kb_entries_fts MATCH :q
        ORDER BY score ASC LIMIT 1;
        """
        row = db.session.execute(text(sql), {"q": pergunta}).mappings().first()
        return dict(row) if row else None
    except Exception as e:
        print(f"Erro na busca KB: {e}")
        return None

# ----------------------
# Internals
# ----------------------

# --- Respostas prontas (mock) turbinadas ---

def _kw(s):  # helper
    return (s or "").lower().strip()

def _match_any(text, *words):
    t = _kw(text)
    return any(w in t for w in words)

def generate_mock_response(message):
    """
    IA simulada para quando não há OpenAI.
    Usa intents simples baseadas em palavras-chave (com sinônimos) + respostas ricas.
    Seguro para produção: não quebra nada, só retorna string.
    """
    msg = _kw(message)

    # ====== INTENTS ESPECÍFICAS (ordem importa) ======
    # 1) Status de empenho por número
    if _match_any(msg, "status", "situação") and _match_any(msg, "empenho", "empenhos"):
        return (
            "Para consultar o **status de um empenho**:\n"
            "1) Vá em **Empenhos → Listar**\n"
            "2) Use a busca pelo **número do empenho** ou **fornecedor**\n"
            "3) Na coluna *Status* você vê: PENDENTE, APROVADO, LIQUIDADO, PAGO, etc.\n"
            "Dica: no filtro avançado dá pra combinar **período**, **contrato** e **valor**."
        )

    # 2) Como criar empenho
    if _match_any(msg, "criar empenho", "novo empenho", "cadastrar empenho", "inserir empenho"):
        return (
            "Para **criar um empenho**:\n"
            "• Acesse **Empenhos → Novo**\n"
            "• Preencha: número, data, fornecedor, objeto, valores (empenhado/liquido/retenção)\n"
            "• (Opcional) amarre a um **contrato** ou **pregão**\n"
            "• Salve e acompanhe o status no fluxo (PENDENTE → APROVADO → LIQUIDADO → PAGO)"
        )

    # 3) Notas Fiscais: cadastrar/ligar ao empenho
    if _match_any(msg, "nota fiscal", "nf", "notas fiscais", "lancar nota", "cadastrar nota"):
        return (
            "Para **lançar uma Nota Fiscal**:\n"
            "1) Vá em **Notas Fiscais → Nova**\n"
            "2) Informe **empenho vinculado**, **data de emissão**, **valor líquido** e **vencimento**\n"
            "3) Status típico: EM_ABERTO → PROCESSANDO → PAGO\n"
            "Dica: no relatório financeiro você vê **pagas vs em aberto** por período."
        )

    # 4) Relatórios
    if _match_any(msg, "relatório", "relatorios", "relatorio", "dashboard", "analítico", "analytics"):
        return (
            "Relatórios disponíveis:\n"
            "• **Relatório Filtrado**: filtros por data, status, contrato, pregão, fornecedor, valor\n"
            "• **Financeiro**: empenhado, líquido, retenções, fluxo semanal e comparativo anual\n"
            "• **Operacional**: produtividade, prazos (vencendo/vencidos) e distribuição de status\n"
            "• **Analytics**: tendências (90d), top fornecedores, KPIs (tempo médio, execução, valor médio)\n"
            "Exportes: Excel (habilitado), PDF/Backup (quando ativados)."
        )

    # 5) Contratos: criar/editar/aditivos
    if _match_any(msg, "contrato", "contratos"):
        if _match_any(msg, "aditivo", "aditivos", "apostilamento"):
            return (
                "Para **aditivos contratuais**:\n"
                "• Abra o **Contrato** → aba **Aditivos** → **Novo Aditivo**\n"
                "• Tipos comuns: **prorrogação de prazo** e **reequilíbrio/valor**\n"
                "• O sistema atualiza o **prazo vigente** e o **valor total** automaticamente."
            )
        return (
            "Sobre **Contratos**:\n"
            "• Cadastre em **Contratos → Novo** (nº, objeto, fornecedor, valor, datas)\n"
            "• Status: ATIVO, FINALIZADO, CANCELADO\n"
            "• Você pode vincular **empenhos** e **notas** ao contrato para visão 360°."
        )

    # 6) Fornecedores
    if _match_any(msg, "fornecedor", "fornecedores", "cadastrar fornecedor"):
        return (
            "Os **fornecedores** são preenchidos nos próprios **Empenhos/Contratos**.\n"
            "Nos relatórios você enxerga o **top fornecedores por valor** e **quantidade de empenhos**."
        )

    # 7) Permissões / usuários
    if _match_any(msg, "usuário", "usuarios", "permissão", "permissoes", "papel", "role", "acesso"):
        return (
            "Permissões de acesso:\n"
            "• **Administrador**: tudo\n"
            "• **Gestor**: contratos, empenhos, relatórios\n"
            "• **Operador**: lançamentos e consultas\n"
            "Pedir ajuste de perfil ao **admin** do sistema."
        )

    # 8) Exportar / Excel / PDF
    if _match_any(msg, "exportar", "excel", "xlsx", "planilha", "baixar relatorio", "pdf", "imprimir"):
        return (
            "Para **exportar**:\n"
            "• No **Relatório Filtrado**, clique **Exportar Excel**\n"
            "• Limite de ~10.000 registros por exportação (use filtros se passar)\n"
            "• PDF e Backup podem estar temporariamente desabilitados."
        )

    # 9) Prazos / vencimentos / alertas
    if _match_any(msg, "vencendo", "vencidos", "prazo", "vencimento", "alerta", "atraso"):
        return (
            "Prazos e alertas:\n"
            "• **Empenhos vencendo** (30 dias) e **vencidos** aparecem no dashboard e relatórios\n"
            "• **Notas vencidas** e **vencendo** (7 dias) também geram alertas\n"
            "• Use o filtro por período p/ priorizar tratativas."
        )

    # 10) Dúvidas de busca/filtros
    if _match_any(msg, "buscar", "pesquisa", "filtrar", "busca", "filtragem"):
        return (
            "Dicas de **filtro**:\n"
            "• Combine **Data início/fim** com **Status** para listas objetivas\n"
            "• Use **contrato, pregão, fornecedor** e **faixa de valor**\n"
            "• Ordene por **data** ou **valor** conforme a necessidade."
        )

    # 11) Login / sessão
    if _match_any(msg, "login", "logar", "senha", "acessar", "não consigo entrar", "nao consigo entrar"):
        return (
            "Problemas de **login**:\n"
            "• Verifique usuário/senha\n"
            "• Se sessão expirar, faça login novamente\n"
            "• Caso persista, peça ao **admin** para redefinir credenciais."
        )

    # 12) Backup / restauração
    if _match_any(msg, "backup", "restaurar", "restauração", "cópia", "exportar banco"):
        return (
            "Backup do sistema:\n"
            "• Rotina de backup pode estar desabilitada nesta instalação\n"
            "• Em produção, recomenda-se **backup diário** do SQLite/postgres\n"
            "• Para restore, contate o administrador de TI."
        )

    # 13) Erros comuns
    if _match_any(msg, "erro", "bug", "travar", "travou"):
        return (
            "Se ocorrer algum **erro**:\n"
            "• Recarregue a página e tente novamente\n"
            "• Verifique se os campos obrigatórios estão preenchidos\n"
            "• Se persistir, copie a mensagem de erro e informe o **admin**."
        )

    # 14) KPIs / métricas
    if _match_any(msg, "kpi", "métricas", "indicadores", "tendência", "tendencias"):
        return (
            "KPIs e tendências (menu **Analytics**):\n"
            "• **Tempo médio** de processamento de empenhos\n"
            "• **Taxa de execução** (liquidados/pagos)\n"
            "• **Valor médio** por empenho e **top fornecedores**\n"
            "• **Variação** (90d vs 90d anterior)."
        )

    # 15) Ajuda / onboarding
    if _match_any(msg, "ajuda", "help", "como usar", "manual", "tutorial"):
        return (
            "Posso ajudar com:\n"
            "• Criar empenhos, lançar notas e vincular contratos\n"
            "• Relatórios financeiros/operacionais\n"
            "• Dúvidas de filtros e exportações\n"
            "• **Lei 14.133/2021** (Nova Lei de Licitações)\n"
            "Diga o que você precisa que eu te guio passo a passo."
        )

    # ====== LEI 14.133/2021 - NOVA LEI DE LICITAÇÕES ======
    # 16) Lei 14.133 - conceitos gerais
    if _match_any(msg, "lei 14.133", "nova lei", "lei de licitações", "lei 14133"):
        return (
            "**Lei 14.133/2021 - Nova Lei de Licitações**\n"
            "• Substitui a Lei 8.666/93, Lei do Pregão e RDC\n"
            "• **Obrigatória desde 1º/04/2023**\n"
            "• Modalidades: Concorrência, Pregão, Concurso, Leilão, Diálogo Competitivo\n"
            "• **Extintas**: Convite e Tomada de Preços\n"
            "Quer saber sobre **modalidades**, **prazos**, **fases** ou **limites**?"
        )

    # 17) Modalidades de licitação
    if _match_any(msg, "modalidades", "pregão", "concorrência", "diálogo competitivo", "leilão", "concurso"):
        if _match_any(msg, "pregão", "pregao"):
            return (
                "**Pregão Eletrônico** (Nova Lei):\n"
                "• Para **bens e serviços comuns**\n"
                "• Prazo mínimo de publicidade: **8 dias úteis**\n"
                "• Inversão de fases (julgamento antes da habilitação)\n"
                "• Modalidade mais utilizada atualmente"
            )
        elif _match_any(msg, "diálogo", "dialogo", "competitivo"):
            return (
                "**Diálogo Competitivo** (novidade da Lei 14.133):\n"
                "• Para **contratações complexas**\n"
                "• Administração dialoga com licitantes antes da proposta final\n"
                "• Prazo mínimo: **25 dias**\n"
                "• Usado quando a solução não está clara no início"
            )
        return (
            "**Modalidades na Lei 14.133/21**:\n"
            "• **Concorrência**: obras/serviços de maior valor\n"
            "• **Pregão**: bens/serviços comuns (mais usado)\n"
            "• **Concurso**: trabalhos técnicos/artísticos\n"
            "• **Leilão**: alienação de bens\n"
            "• **Diálogo Competitivo**: contratações complexas"
        )

    # 18) Fases da licitação
    if _match_any(msg, "fases", "preparatória", "julgamento", "habilitação", "inversão"):
        return (
            "**Fases da Licitação** (Lei 14.133):\n"
            "1) **Preparatória**: planejamento, estudo técnico, termo de referência\n"
            "2) **Divulgação**: edital no PNCP\n"
            "3) **Propostas**: apresentação pelos licitantes\n"
            "4) **Julgamento**: análise das propostas\n"
            "5) **Habilitação**: verificação de documentos (após julgamento)\n"
            "6) **Recursos**: impugnações\n"
            "7) **Homologação**: aprovação final"
        )

    # 19) Limites e dispensa
    if _match_any(msg, "dispensa", "limites", "inexigibilidade", "100 mil", "50 mil"):
        return (
            "**Limites de Dispensa** (Lei 14.133):\n"
            "• **Até R$ 100 mil**: obras e serviços de engenharia\n"
            "• **Até R$ 50 mil**: bens e outros serviços\n"
            "\n**Inexigibilidade**: quando a competição é inviável\n"
            "• Fornecedor exclusivo\n"
            "• Serviços de notória especialização\n"
            "• Artistas consagrados"
        )

    # 20) Prazos da nova lei
    if _match_any(msg, "prazos", "publicidade", "impugnação", "recursos", "8 dias"):
        return (
            "**Prazos Mínimos** (Lei 14.133):\n"
            "• **Pregão/Concorrência**: 8 dias úteis\n"
            "• **Leilão**: 15 dias\n"
            "• **Concurso**: 45 dias\n"
            "• **Diálogo Competitivo**: 25 dias\n"
            "\n**Impugnação**: 5 dias úteis (cidadãos) / 2 dias (licitantes)\n"
            "**Recursos**: 3 dias úteis"
        )

    # 21) PNCP e publicação
    if _match_any(msg, "pncp", "portal", "publicação", "edital", "divulgação"):
        return (
            "**Portal Nacional de Contratações Públicas (PNCP)**:\n"
            "• **Obrigatório** para todos os órgãos públicos\n"
            "• Publica: editais, atas, dispensas, inexigibilidades, contratos\n"
            "• Substitui o DOU para licitações\n"
            "• Garante transparência e acesso à informação"
        )

    # 22) Planejamento e estudo técnico
    if _match_any(msg, "planejamento", "estudo técnico", "termo de referência", "pac", "plano anual"):
        return (
            "**Planejamento na Lei 14.133**:\n"
            "• **PAC**: Plano Anual de Contratações (obrigatório)\n"
            "• **Estudo Técnico Preliminar**: justifica a necessidade\n"
            "• **Termo de Referência**: descreve objeto e condições\n"
            "• **Análise de Riscos**: identifica e mitiga riscos\n"
            "• **Estimativa de Custos**: orçamento (pode ser sigiloso)"
        )

    # 23) Contratos e gestão
    if _match_any(msg, "duração", "reajuste", "repactuação", "fiscal", "gestor"):
        return (
            "**Contratos na Lei 14.133**:\n"
            "• **Duração**: até 5 anos (10 em serviços contínuos, 15 em tecnologia)\n"
            "• **Reajuste**: anual por índice oficial\n"
            "• **Repactuação**: serviços contínuos com mão de obra\n"
            "• **Fiscal**: acompanha execução diária\n"
            "• **Gestor**: responsável geral pelo contrato"
        )

    # 24) Sanções e penalidades
    if _match_any(msg, "sanções", "penalidades", "multa", "inidoneidade", "impedimento"):
        return (
            "**Sanções** (Lei 14.133):\n"
            "• **Advertência**: para infrações leves\n"
            "• **Multa**: percentual sobre o valor\n"
            "• **Impedimento**: até 3 anos para licitar\n"
            "• **Inidoneidade**: válida em todo o país\n"
            "Aplicadas conforme gravidade da infração"
        )

    # 25) Registro de preços
    if _match_any(msg, "registro de preços", "ata", "12 meses", "arp"):
        return (
            "**Sistema de Registro de Preços**:\n"
            "• **Ata**: compromisso para futuras contratações\n"
            "• **Vigência**: até 12 meses (prorrogável por mais 12)\n"
            "• Fornecedores se comprometem com preços registrados\n"
            "• Permite contratações conforme demanda"
        )

    # ====== SAUDAÇÕES / PEQUENO TALK ======
    if _match_any(msg, "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"):
        return "Olá! 👋 Sou o assistente do Sistema Municipal. Em que posso ajudar hoje?"

    # ====== FALLBACK ======
    # 26) Perguntas específicas da Lei 14.133 - Parte 1
    if _match_any(msg, "quando obrigatória", "1 abril 2023", "abril 2023"):
        return "A Lei 14.133/21 **passou a ser obrigatória em 1º de abril de 2023** para todos os órgãos e entidades públicas."

    if _match_any(msg, "fase preparatória", "preparatoria"):
        return (
            "**Fase Preparatória**: planejamento da contratação incluindo:\n"
            "• Estudo técnico preliminar\n"
            "• Análise de riscos\n"
            "• Estimativa de custos\n"
            "• Elaboração do termo de referência"
        )

    if _match_any(msg, "critérios de julgamento", "criterios", "menor preço", "melhor técnica"):
        return (
            "**Critérios de Julgamento** (Lei 14.133):\n"
            "• Menor preço\n"
            "• Maior desconto\n"
            "• Melhor técnica\n"
            "• Técnica e preço\n"
            "• Maior lance ou oferta\n"
            "• Maior retorno econômico"
        )

    if _match_any(msg, "agente de contratação", "comissão"):
        return "**Agente de Contratação**: servidor designado para conduzir a licitação, podendo atuar sozinho ou em comissão."

    if _match_any(msg, "orçamento sigiloso", "valor estimado"):
        return "**Orçamento Sigiloso**: valor estimado pela Administração que pode ser mantido em sigilo até o término da licitação para evitar manipulação."

    if _match_any(msg, "matriz de riscos", "riscos"):
        return "**Matriz de Riscos**: anexo contratual que define responsabilidades da Administração e do contratado diante de eventos imprevistos."

    # 27) Perguntas específicas da Lei 14.133 - Parte 2
    if _match_any(msg, "gestão de riscos", "identificação", "análise"):
        return "**Gestão de Riscos**: identificação, análise e tratamento de riscos da contratação, **obrigatória** na Nova Lei."

    if _match_any(msg, "bens comuns", "serviços comuns", "padrões de desempenho"):
        return "**Bens e Serviços Comuns**: aqueles cujos padrões de desempenho podem ser objetivamente definidos no edital, permitindo comparabilidade."

    if _match_any(msg, "bens especiais", "serviços especiais", "especificações técnicas"):
        return "**Bens e Serviços Especiais**: os que exigem especificações técnicas diferenciadas, não enquadrados como comuns."

    if _match_any(msg, "princípios", "legalidade", "transparência", "eficiência"):
        return (
            "**Princípios da Lei 14.133**:\n"
            "• Legalidade, impessoalidade, moralidade\n"
            "• Igualdade, publicidade, eficiência\n"
            "• **Planejamento, transparência, segurança jurídica**"
        )

    if _match_any(msg, "controle interno", "controle externo", "tribunais de contas"):
        if _match_any(msg, "externo", "tribunais"):
            return "**Controle Externo**: exercido pelos Tribunais de Contas, que fiscalizam a legalidade e gestão das contratações públicas."
        return "**Controle Interno**: estrutura da Administração responsável por acompanhar a legalidade, eficiência e economicidade das contratações."

    if _match_any(msg, "governança", "integridade", "transparência"):
        return "**Governança das Contratações**: práticas e mecanismos para assegurar integridade, eficiência e transparência nos processos de compras públicas."

    # ====== LEI 14.133 - QUESTÕES PRÁTICAS DE IMPLEMENTAÇÃO ======
    # 28) Estudo Técnico Preliminar (ETP)
    if _match_any(msg, "estudo técnico preliminar", "etp", "como fazer etp"):
        return (
            "**Como fazer o Estudo Técnico Preliminar (ETP)**:\n"
            "1️⃣ **Descrição da necessidade**\n"
            "2️⃣ **Levantamento de soluções existentes**\n"
            "3️⃣ **Justificativa da escolha**\n"
            "4️⃣ **Estimativa de custos**\n"
            "5️⃣ **Análise de viabilidade**\n"
            "6️⃣ **Avaliação de riscos**\n"
            "O ETP serve de **base para o termo de referência**."
        )

    # 29) Termo de Referência - elaboração
    if _match_any(msg, "como elaborar", "termo de referência", "elaborar termo"):
        return (
            "**Como elaborar o Termo de Referência**:\n"
            "• **Objeto detalhado** e justificativa da contratação\n"
            "• **Requisitos técnicos** e critérios de medição\n"
            "• **Forma de pagamento** e prazos\n"
            "• **Garantias** e obrigações das partes\n"
            "• **Penalidades** aplicáveis"
        )

    # 30) Orçamento estimado - pesquisa de preços
    if _match_any(msg, "orçamento estimado", "pesquisa de preços", "como montar orçamento"):
        return (
            "**Como montar o orçamento estimado**:\n"
            "📊 **Pesquisa em pelo menos 3 fontes**:\n"
            "• **Contratos semelhantes** no PNCP\n"
            "• **Painéis de preços** de órgãos oficiais\n"
            "• **Consulta a fornecedores**\n"
            "🎯 A **média ponderada** embasa o valor da licitação"
        )

    # 31) PAC - montagem prática
    if _match_any(msg, "como montar pac", "plano anual contratações", "montar plano anual"):
        return (
            "**Como montar o Plano Anual de Contratações (PAC)**:\n"
            "1️⃣ **Consolidar demandas** das secretarias\n"
            "2️⃣ **Justificar necessidades** e priorizar recursos\n"
            "3️⃣ **Estimar valores** e cronograma\n"
            "4️⃣ **Publicar no PNCP** até o prazo legal\n"
            "É a **lista de todas as contratações** previstas para o exercício."
        )

    # 32) Passo a passo da licitação
    if _match_any(msg, "passo a passo", "fluxo licitação", "etapas licitação"):
        return (
            "**Passo a passo da licitação** (Lei 14.133):\n"
            "1️⃣ **Planejamento**: ETP, TR, orçamento, PAC\n"
            "2️⃣ **Publicação** do edital no PNCP\n"
            "3️⃣ **Recebimento** de propostas\n"
            "4️⃣ **Julgamento** das propostas\n"
            "5️⃣ **Habilitação** do vencedor\n"
            "6️⃣ **Recursos** (se houver)\n"
            "7️⃣ **Homologação** e adjudicação\n"
            "8️⃣ **Assinatura** do contrato"
        )

    # 33) Fiscalização de contratos
    if _match_any(msg, "como fiscalizar", "fiscalizar contrato", "fiscal contrato"):
        return (
            "**Como fiscalizar um contrato municipal**:\n"
            "🔍 **O fiscal deve**:\n"
            "• **Acompanhar** entregas e serviços\n"
            "• **Registrar** em relatórios\n"
            "• **Atestar** notas fiscais\n"
            "• **Comunicar** irregularidades\n"
            "• **Propor penalidades** quando cabível"
        )

    # 34) Registro de riscos prático
    if _match_any(msg, "como registrar riscos", "registrar riscos", "matriz riscos prática"):
        return (
            "**Como registrar riscos na contratação**:\n"
            "📋 **A matriz de riscos deve**:\n"
            "• **Identificar** eventos possíveis (atrasos, falhas técnicas, reajustes)\n"
            "• **Avaliar impacto** de cada risco\n"
            "• **Definir responsabilidades**: contratado ou Administração\n"
            "• **Estabelecer** medidas de mitigação"
        )

    # 35) Responsabilidades do gestor
    if _match_any(msg, "responsabilidades gestor", "gestor contrato", "o que faz gestor"):
        return (
            "**Responsabilidades do gestor do contrato**:\n"
            "⚖️ **Garante** execução fiel do objeto\n"
            "💰 **Autoriza** pagamentos\n"
            "🤝 **Interage** com o fiscal\n"
            "📢 **Comunica** falhas\n"
            "🏛️ **Representa** a Administração perante o contratado"
        )

    # 36) Aplicação de penalidades
    if _match_any(msg, "como aplicar penalidades", "aplicar penalidades", "penalizar contratado"):
        return (
            "**Como aplicar penalidades ao contratado**:\n"
            "1️⃣ **Fiscal relata** a ocorrência\n"
            "2️⃣ **Gestor notifica** o contratado\n"
            "3️⃣ **Abre prazo** para defesa\n"
            "4️⃣ **Autoridade decide**: advertência, multa, impedimento ou inidoneidade\n"
            "5️⃣ **Registra** a penalidade no PNCP"
        )

    # 37) Obras públicas - cuidados especiais
    if _match_any(msg, "obras públicas", "projeto básico", "cronograma físico"):
        return (
            "**O que observar em obras públicas**:\n"
            "📐 **Projeto básico** completo\n"
            "📅 **Cronograma** físico-financeiro\n"
            "💰 **Orçamento** detalhado\n"
            "📋 **ART/RRT** dos responsáveis técnicos\n"
            "🔍 **Análise de viabilidade**\n"
            "⚠️ **Matriz de riscos** específica para obras"
        )

    # ====== FALLBACK ORIGINAL ======
    if _match_any(msg, "empenho", "empenhos"):
        return "Empenhos reservam recurso orçamentário. Quer **criar**, **consultar status** ou **exportar**?"

    if _match_any(msg, "contrato", "contratos"):
        return "Quer **cadastrar contrato**, **aditivo** ou **ver situação** dos contratos ativos?"

    if _match_any(msg, "nota", "notas", "nf", "nota fiscal", "notas fiscais"):
        return "Sobre **notas fiscais**: posso explicar **lançamento**, **status** ou **pagamentos**. O que deseja?"

    # Default bem-educado
    return (
        "Entendi. Posso falar sobre **empenhos, contratos, notas, relatórios, KPIs, prazos** e **exportações**.\n"
        "Diga em poucas palavras o que precisa (ex.: *relatório financeiro do mês*, *criar empenho*, *aditivo de contrato*)."
    )

def _generate_ai_response(user_text: str) -> str:
    """
    Geração de resposta inteligente:
    1º - Busca no Knowledge Base (KB) 
    2º - Se não achou, usa OpenAI (se disponível)
    3º - Fallback para respostas mock estáveis
    """
    
    # 🔎 1º PRIORIDADE: Buscar no Knowledge Base
    kb_match = kb_best_match(user_text)
    if kb_match:
        return f"📚 **KB**: {kb_match['answer']}\n\n*Baseado na pergunta: \"{kb_match['question']}\"*"
    
    # 🤖 2º PRIORIDADE: OpenAI (se disponível)
    if OPENAI_AVAILABLE:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente para gestão municipal (empenhos/contratos). Seja claro e útil."},
                    {"role": "user", "content": user_text}
                ],
                max_tokens=500,
                temperature=0.7,
                timeout=20
            )
            return f"🤖 **IA**: {resp.choices[0].message['content']}"
        except Exception as e:
            # Se a API falhar, não quebra o fluxo
            pass
    
    # 💡 3º PRIORIDADE: Fallback mock estável  
    return f"💡 **Sistema**: {generate_mock_response(user_text)}"

def _mock_response(text: str) -> str:
    """Função legada mantida para compatibilidade"""
    return generate_mock_response(text)
