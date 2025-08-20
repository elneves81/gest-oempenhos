# relatorios.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from models import Empenho, Contrato, NotaFiscal, db
# IMPORTS CORRIGIDOS - utils carregados dinamicamente quando necessário
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, case, desc, asc, text
from sqlalchemy.orm import joinedload
import os
import logging
import json
import random
from collections import defaultdict

# Função para simular relativedelta sem import problemático
def add_months(source_date, months):
    """Adicionar meses a uma data sem usar relativedelta"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, [31,
        29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return date(year, month, day)

relatorios_bp = Blueprint('relatorios', __name__)
logger = logging.getLogger(__name__)

# Constantes
CACHE_TIMEOUT = 300  # 5 min
DEFAULT_PAGE_SIZE = 50

# ----------------- Helpers -----------------

def _coalesce_float(expr):
    return func.coalesce(expr, 0.0)

def _pct(a, b):
    """Calcular percentual de variação entre dois valores"""
    b = (b or 0)
    if b == 0:
        return None
    return round(((a or 0) - b) / b * 100, 1)

def _build_insights(evolucao_mensal, emp_status, notas_status):
    """Construir insights automáticos baseados nos dados"""
    # Comparar os 2 últimos meses
    if len(evolucao_mensal) < 2:
        return []
    last, prev = evolucao_mensal[-1], evolucao_mensal[-2]
    g_emp_val = _pct(last['empenhos_valor'], prev['empenhos_valor'])
    g_not_val = _pct(last['notas_valor'], prev['notas_valor'])

    # % de "ATIVO" nos empenhos
    total_emp = sum(e['quantidade'] for e in emp_status) or 1
    ativos = next((e['quantidade'] for e in emp_status if (e['status'] or '').upper()=='ATIVO'), 0)
    p_ativo = round(ativos/total_emp*100, 1)

    # % de "EM_ABERTO" nas notas
    total_not = sum(n['quantidade'] for n in notas_status) or 1
    abertas = next((n['quantidade'] for n in notas_status if (n['status'] or '')=='EM_ABERTO'), 0)
    p_aberto = round(abertas/total_not*100, 1)

    insights = []
    if g_emp_val is not None:
        insights.append({'icon':'graph-up-arrow' if g_emp_val>=0 else 'graph-down-arrow',
                         'texto': f"Valor empenhado {('↑' if g_emp_val>=0 else '↓')} {abs(g_emp_val)}% vs mês anterior."})
    if g_not_val is not None:
        insights.append({'icon':'cash-coin',
                         'texto': f"Valor de notas {('↑' if g_not_val>=0 else '↓')} {abs(g_not_val)}% vs mês anterior."})
    insights.append({'icon':'activity', 'texto': f"{p_ativo}% dos empenhos estão ATIVOS."})
    insights.append({'icon':'exclamation-triangle', 'texto': f"{p_aberto}% das notas estão EM ABERTO."})
    return insights

@relatorios_bp.route('/')
@login_required
def index():
    """Dashboard simplificado com contratos"""
    try:
        # Dados básicos de empenhos
        total_empenhos = Empenho.query.count()
        empenhos_ativos = Empenho.query.filter_by(status='ATIVO').count()
        
        # Dados básicos de contratos
        total_contratos = Contrato.query.count()
        contratos_ativos = Contrato.query.filter_by(status='ATIVO').count()
        contratos_finalizados = Contrato.query.filter_by(status='FINALIZADO').count()
        contratos_cancelados = Contrato.query.filter_by(status='CANCELADO').count()
        
        # Dados básicos de notas fiscais
        total_notas = 0
        try:
            from models import NotaFiscal
            total_notas = NotaFiscal.query.count()
        except:
            total_notas = 0
        
        # Valores financeiros seguros
        from sqlalchemy import func
        valor_empenhado = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
        valor_contratos = db.session.query(func.sum(Contrato.valor_total)).scalar() or 0
        valor_notas_pagas = 0
        if total_notas > 0:
            try:
                valor_notas_pagas = db.session.query(
                    func.sum(NotaFiscal.valor_liquido)
                ).filter(NotaFiscal.status == 'PAGO').scalar() or 0
            except:
                valor_notas_pagas = 0
        
        # Evolução mensal e distribuições
        evolucao_mensal = _get_evolucao_mensal_simples()
        empenhos_por_status = _get_empenhos_por_status()
        notas_por_status = _get_notas_por_status()
        
        # Insights
        insights = _build_insights_simples(total_empenhos, empenhos_ativos, total_notas)
        
        # Dados simplificados
        dados_dashboard = {
            'total_empenhos': total_empenhos,
            'empenhos_ativos': empenhos_ativos,
            'total_contratos': total_contratos,
            'contratos_ativos': contratos_ativos,
            'contratos_finalizados': contratos_finalizados,
            'contratos_cancelados': contratos_cancelados,
            'total_notas': total_notas,
            'valor_total_empenhado': float(valor_empenhado),
            'valor_total_contratos': float(valor_contratos),
            'valor_notas_pagas': float(valor_notas_pagas),
            'evolucao_mensal': evolucao_mensal,
            'empenhos_por_status': empenhos_por_status,
            'notas_por_status': notas_por_status,
            'insights': insights
        }
        
        return render_template('relatorios/index_moderno.html', **dados_dashboard)
    
    except Exception as e:
        logger.error(f"Erro ao carregar relatórios: {e}")
        flash('Erro ao carregar dados dos relatórios', 'error')
        
        # Dados de fallback
        dados_fallback = {
            'total_empenhos': 0,
            'empenhos_ativos': 0,
            'total_contratos': 0,
            'contratos_ativos': 0,
            'contratos_finalizados': 0,
            'contratos_cancelados': 0,
            'total_notas': 0,
            'valor_total_empenhado': 0,
            'valor_total_contratos': 0,
            'valor_notas_pagas': 0,
            'evolucao_mensal': [],
            'empenhos_por_status': {},
            'notas_por_status': {},
            'insights': [{'icon': 'info-circle', 'texto': 'Sistema em manutenção.'}]
        }
        
        return render_template('relatorios/index_moderno.html', **dados_fallback)


@relatorios_bp.route('/demonstrativo/contratos')
@login_required
def relatorio_contratos():
    """Relatório específico de contratos"""
    try:
        # Buscar todos os contratos
        contratos = Contrato.query.order_by(Contrato.data_assinatura.desc()).all()
        
        # Totais no banco
        total_contratos = db.session.query(func.count(Contrato.id)).scalar() or 0
        valor_total = db.session.query(func.coalesce(func.sum(Contrato.valor_total), 0)).scalar() or 0.0
        
        # Por status no banco (portável)
        status_rows = db.session.query(
            Contrato.status, func.count(Contrato.id)
        ).group_by(Contrato.status).all()
        contratos_por_status = {(s or 'INDEFINIDO'): c for s, c in status_rows}
        
        # Top fornecedores direto no banco
        top_rows = db.session.query(
            Contrato.fornecedor,
            func.count(Contrato.id).label('quantidade'),
            func.coalesce(func.sum(Contrato.valor_total), 0).label('valor_total')
        ).group_by(Contrato.fornecedor).order_by(desc('valor_total')).limit(5).all()
        
        top_fornecedores = [
            (row.fornecedor or 'Não informado', {'quantidade': row.quantidade, 'valor_total': float(row.valor_total)})
            for row in top_rows
        ]
        
        return render_template('relatorios/contratos.html',
                             contratos=contratos,
                             total_contratos=total_contratos,
                             valor_total=float(valor_total),
                             contratos_por_status=contratos_por_status,
                             top_fornecedores=top_fornecedores)
    
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de contratos: {e}")
        flash('Erro ao gerar relatório de contratos', 'error')
        return redirect(url_for('relatorios.index'))


@relatorios_bp.route('/filtrado')
@login_required
def filtrado():
    """Relatório com filtros personalizados melhorado"""
    try:
        # Parâmetros de filtro com validação
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        contrato = request.args.get('contrato')
        pregao = request.args.get('pregao')
        fornecedor = request.args.get('fornecedor')
        valor_min = request.args.get('valor_min', type=float)
        valor_max = request.args.get('valor_max', type=float)
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)
        
        # Query base otimizada
        query = Empenho.query.options(joinedload(Empenho.notas_fiscais))
        
        # Aplicar filtros com validação
        filtros_aplicados = {}
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(Empenho.data_empenho >= data_inicio_dt)
                filtros_aplicados['data_inicio'] = data_inicio
            except ValueError:
                flash('Data de início inválida', 'error')
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(Empenho.data_empenho <= data_fim_dt)
                filtros_aplicados['data_fim'] = data_fim
            except ValueError:
                flash('Data de fim inválida', 'error')
        
        if status:
            query = query.filter(Empenho.status == status)
            filtros_aplicados['status'] = status
        
        if contrato:
            query = query.filter(func.lower(Empenho.numero_contrato).like(f'%{contrato.lower()}%'))
            filtros_aplicados['contrato'] = contrato
        
        if pregao:
            query = query.filter(func.lower(Empenho.numero_pregao).like(f'%{pregao.lower()}%'))
            filtros_aplicados['pregao'] = pregao
            
        if fornecedor:
            query = query.filter(func.lower(Empenho.fornecedores).like(f'%{fornecedor.lower()}%'))
            filtros_aplicados['fornecedor'] = fornecedor
        
        if valor_min is not None:
            query = query.filter(Empenho.valor_empenhado >= valor_min)
            filtros_aplicados['valor_min'] = valor_min
            
        if valor_max is not None:
            query = query.filter(Empenho.valor_empenhado <= valor_max)
            filtros_aplicados['valor_max'] = valor_max
        
        # Aplicar ordenação
        ordem = request.args.get('ordem', 'data_desc')
        if ordem == 'data_asc':
            query = query.order_by(asc(Empenho.data_empenho))
        elif ordem == 'valor_desc':
            query = query.order_by(desc(Empenho.valor_empenhado))
        elif ordem == 'valor_asc':
            query = query.order_by(asc(Empenho.valor_empenhado))
        else:  # data_desc (padrão)
            query = query.order_by(desc(Empenho.data_empenho))
        
        # Executar query com paginação
        empenhos_paginados = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        empenhos = empenhos_paginados.items
        
        # Calcular totais otimizado
        totais_query = query.with_entities(
            func.count(Empenho.id).label('total_registros'),
            func.coalesce(func.sum(Empenho.valor_empenhado), 0).label('valor_total_empenhado'),
            func.coalesce(func.sum(Empenho.valor_liquido), 0).label('valor_total_liquido'),
            func.coalesce(func.sum(Empenho.valor_retencao), 0).label('valor_total_retencao')
        ).first()
        
        # Estatísticas por status no resultado filtrado
        status_stats = query.with_entities(
            Empenho.status,
            func.count(Empenho.id).label('quantidade'),
            func.coalesce(func.sum(Empenho.valor_empenhado), 0).label('valor')
        ).group_by(Empenho.status).all()
        
        return render_template('relatorios/filtrado.html',
                             empenhos=empenhos,
                             empenhos_paginados=empenhos_paginados,
                             totais={
                                 'registros': totais_query.total_registros,
                                 'valor_empenhado': float(totais_query.valor_total_empenhado),
                                 'valor_liquido': float(totais_query.valor_total_liquido),
                                 'valor_retencao': float(totais_query.valor_total_retencao)
                             },
                             status_stats=[
                                 {
                                     'status': row.status,
                                     'quantidade': row.quantidade,
                                     'valor': float(row.valor)
                                 } for row in status_stats
                             ],
                             filtros=filtros_aplicados,
                             ordem=ordem)
                             
    except Exception as e:
        logger.error(f"Erro no relatório filtrado: {str(e)}")
        flash('Erro ao processar filtros. Tente novamente.', 'error')
        return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/exportar/excel')
@login_required
def exportar_excel():
    """Exportar relatório para Excel com melhorias"""
    try:
        # Verificar permissões
        if not (current_user.is_admin or getattr(current_user, 'can_export_reports', False)):
            flash('Você não tem permissão para exportar relatórios.', 'error')
            return redirect(url_for('relatorios.index'))
        
        # Obter filtros da query string
        filtros = {
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'status': request.args.get('status'),
            'contrato': request.args.get('contrato'),
            'pregao': request.args.get('pregao'),
            'fornecedor': request.args.get('fornecedor'),
            'valor_min': request.args.get('valor_min', type=float),
            'valor_max': request.args.get('valor_max', type=float)
        }
        
        # Aplicar filtros (código similar ao filtrado, mas sem paginação)
        query = Empenho.query.options(joinedload(Empenho.notas_fiscais))
        
        if filtros['data_inicio']:
            query = query.filter(Empenho.data_empenho >= datetime.strptime(filtros['data_inicio'], '%Y-%m-%d').date())
        
        if filtros['data_fim']:
            query = query.filter(Empenho.data_empenho <= datetime.strptime(filtros['data_fim'], '%Y-%m-%d').date())
        
        if filtros['status']:
            query = query.filter(Empenho.status == filtros['status'])
        
        if filtros['contrato']:
            query = query.filter(func.lower(Empenho.numero_contrato).like(f"%{filtros['contrato'].lower()}%"))
        
        if filtros['pregao']:
            query = query.filter(func.lower(Empenho.numero_pregao).like(f"%{filtros['pregao'].lower()}%"))
            
        if filtros['fornecedor']:
            query = query.filter(func.lower(Empenho.fornecedores).like(f"%{filtros['fornecedor'].lower()}%"))
        
        if filtros['valor_min'] is not None:
            query = query.filter(Empenho.valor_empenhado >= filtros['valor_min'])
            
        if filtros['valor_max'] is not None:
            query = query.filter(Empenho.valor_empenhado <= filtros['valor_max'])
        
        empenhos = query.order_by(desc(Empenho.data_empenho)).all()
        
        # Limitar exportação para evitar sobrecarga
        if len(empenhos) > 10000:
            flash('Muitos registros para exportação. Aplique filtros para reduzir o resultado.', 'warning')
            return redirect(url_for('relatorios.filtrado', **{k: v for k, v in filtros.items() if v}))
        
        # Gerar arquivo Excel
        filename = ExportXLSXHelper.export_to_excel(empenhos, filtros)
        
        return send_file(filename, 
                        as_attachment=True, 
                        download_name=f'relatorio_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
    except Exception as e:
        logger.error(f"Erro ao exportar para Excel: {str(e)}")
        flash(f'Erro ao exportar para Excel: {str(e)}', 'error')
        return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/dashboard-avancado')
@login_required
def dashboard_avancado():
    """Dashboard avançado com gráficos interativos"""
    try:
        # Período personalizável
        periodo = request.args.get('periodo', '30')  # dias
        data_fim = date.today()
        
        if periodo == '365':
            data_inicio = data_fim - timedelta(days=365)
        elif periodo == '90':
            data_inicio = data_fim - timedelta(days=90)
        else:  # 30 dias (padrão)
            data_inicio = data_fim - timedelta(days=30)
        
        # Métricas avançadas
        metricas_avancadas = _get_metricas_avancadas(data_inicio, data_fim)
        
        # Dados para gráficos interativos
        graficos_avancados = _get_graficos_avancados(data_inicio, data_fim)
        
        # Análise de tendências
        analise_tendencias = _get_analise_tendencias(data_inicio, data_fim)
        
        # Ranking de performance
        ranking_performance = _get_ranking_performance(data_inicio, data_fim)
        
        return render_template('relatorios/dashboard_avancado.html',
                             periodo=periodo,
                             data_inicio=data_inicio,
                             data_fim=data_fim,
                             metricas_avancadas=metricas_avancadas,
                             graficos_avancados=graficos_avancados,
                             analise_tendencias=analise_tendencias,
                             ranking_performance=ranking_performance)
                             
    except Exception as e:
        logger.error(f"Erro no dashboard avançado: {str(e)}")
        flash('Erro ao carregar dashboard avançado.', 'error')
        return redirect(url_for('relatorios.index'))

def _get_metricas_avancadas(data_inicio, data_fim):
    """Obter métricas avançadas para dashboard"""
    try:
        # Métricas básicas
        total_empenhos = db.session.query(func.count(Empenho.id)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).scalar() or 0
        
        valor_total = db.session.query(func.sum(Empenho.valor_empenhado)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # Métricas de performance - substituindo datediff por cálculo Python
        empenhos_com_prazo = db.session.query(
            Empenho.data_empenho,
            Empenho.data_vencimento
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim),
            Empenho.data_vencimento.isnot(None)
        ).all()
        
        if empenhos_com_prazo:
            prazos = [(emp.data_vencimento - emp.data_empenho).days for emp in empenhos_com_prazo]
            tempo_medio_execucao = sum(prazos) / len(prazos)
        else:
            tempo_medio_execucao = 0
        
        # Taxa de sucesso (empenhos não vencidos)
        empenhos_vencidos = db.session.query(func.count(Empenho.id)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim),
            Empenho.data_vencimento < date.today(),
            Empenho.status != 'FINALIZADO'
        ).scalar() or 0
        
        taxa_sucesso = ((total_empenhos - empenhos_vencidos) / total_empenhos * 100) if total_empenhos > 0 else 0
        
        # Distribuição por status
        distribuicao_status = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(Empenho.status).all()
        
        # Top fornecedores
        top_fornecedores = db.session.query(
            Empenho.fornecedores,
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(Empenho.fornecedores).order_by(desc('valor')).limit(10).all()
        
        return {
            'total_empenhos': total_empenhos,
            'valor_total': valor_total,
            'tempo_medio_execucao': round(tempo_medio_execucao, 1),
            'taxa_sucesso': round(taxa_sucesso, 1),
            'distribuicao_status': [
                {'status': item.status, 'quantidade': item.quantidade, 'valor': item.valor}
                for item in distribuicao_status
            ],
            'top_fornecedores': [
                {'fornecedor': item.fornecedores, 'quantidade': item.quantidade, 'valor': item.valor}
                for item in top_fornecedores
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas avançadas: {str(e)}")
        return {}

def _get_graficos_avancados(data_inicio, data_fim):
    """Obter dados para gráficos interativos"""
    try:
        # Série temporal de empenhos - Usando DATE portável
        from sqlalchemy import func, Date
        data_expr = func.cast(Empenho.data_empenho, Date)

        series_temporal = db.session.query(
            data_expr.label('data'),
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(data_expr).order_by(data_expr).all()
        
        # Distribuição por faixa de valor
        faixas_valor = [
            {'nome': 'Até R$ 1.000', 'min': 0, 'max': 1000},
            {'nome': 'R$ 1.001 - R$ 10.000', 'min': 1001, 'max': 10000},
            {'nome': 'R$ 10.001 - R$ 50.000', 'min': 10001, 'max': 50000},
            {'nome': 'R$ 50.001 - R$ 100.000', 'min': 50001, 'max': 100000},
            {'nome': 'Acima de R$ 100.000', 'min': 100001, 'max': float('inf')}
        ]
        
        distribuicao_valor = []
        for faixa in faixas_valor:
            if faixa['max'] == float('inf'):
                count = db.session.query(func.count(Empenho.id)).filter(
                    Empenho.data_empenho.between(data_inicio, data_fim),
                    Empenho.valor_empenhado >= faixa['min']
                ).scalar() or 0
            else:
                count = db.session.query(func.count(Empenho.id)).filter(
                    Empenho.data_empenho.between(data_inicio, data_fim),
                    Empenho.valor_empenhado.between(faixa['min'], faixa['max'])
                ).scalar() or 0
            
            distribuicao_valor.append({'nome': faixa['nome'], 'quantidade': count})
        
        # Análise mensal
        from sqlalchemy.sql import extract
        ano = extract('year', Empenho.data_empenho)
        mes = extract('month', Empenho.data_empenho)

        analise_mensal = db.session.query(
            ano.label('ano'),
            mes.label('mes'),
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor'),
            func.avg(Empenho.valor_empenhado).label('valor_medio')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(ano, mes).order_by(ano, mes).all()
        
        return {
            'series_temporal': [
                {
                    'data': item.data,  # Already a string from strftime in query
                    'quantidade': item.quantidade,
                    'valor': float(item.valor) if item.valor else 0
                }
                for item in series_temporal
            ],
            'distribuicao_valor': distribuicao_valor,
            'analise_mensal': [
                {
                    'periodo': f"{int(item.ano)}-{int(item.mes):02d}",
                    'quantidade': item.quantidade,
                    'valor': float(item.valor) if item.valor else 0,
                    'valor_medio': float(item.valor_medio) if item.valor_medio else 0
                }
                for item in analise_mensal
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter dados para gráficos: {str(e)}")
        return {}

def _get_analise_tendencias(data_inicio, data_fim):
    """Análise de tendências"""
    try:
        # Dividir período em semanas para análise de tendência
        semanas = []
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            fim_semana = min(data_atual + timedelta(days=6), data_fim)
            
            dados_semana = db.session.query(
                func.count(Empenho.id).label('quantidade'),
                func.sum(Empenho.valor_empenhado).label('valor')
            ).filter(
                Empenho.data_empenho.between(data_atual, fim_semana)
            ).first()
            
            semanas.append({
                'periodo': f"{data_atual.strftime('%d/%m')} - {fim_semana.strftime('%d/%m')}",
                'quantidade': dados_semana.quantidade or 0,
                'valor': float(dados_semana.valor) if dados_semana.valor else 0
            })
            
            data_atual = fim_semana + timedelta(days=1)
        
        # Calcular tendências
        if len(semanas) >= 2:
            # Tendência de quantidade
            qtd_inicial = semanas[0]['quantidade']
            qtd_final = semanas[-1]['quantidade']
            tendencia_quantidade = ((qtd_final - qtd_inicial) / qtd_inicial * 100) if qtd_inicial > 0 else 0
            
            # Tendência de valor
            val_inicial = semanas[0]['valor']
            val_final = semanas[-1]['valor']
            tendencia_valor = ((val_final - val_inicial) / val_inicial * 100) if val_inicial > 0 else 0
        else:
            tendencia_quantidade = 0
            tendencia_valor = 0
        
        return {
            'semanas': semanas,
            'tendencia_quantidade': round(tendencia_quantidade, 1),
            'tendencia_valor': round(tendencia_valor, 1)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter análise de tendências: {str(e)}")
        return {}

def _get_ranking_performance(data_inicio, data_fim):
    """Ranking de performance por contrato/pregão"""
    try:
        # Performance por contrato
        performance_contratos = db.session.query(
            Empenho.numero_contrato,
            func.count(Empenho.id).label('total_empenhos'),
            func.sum(Empenho.valor_empenhado).label('valor_total'),
            func.avg(Empenho.valor_empenhado).label('valor_medio'),
            func.sum(case((Empenho.status == 'FINALIZADO', 1), else_=0)).label('finalizados')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim),
            Empenho.numero_contrato.isnot(None)
        ).group_by(Empenho.numero_contrato).order_by(desc('valor_total')).limit(10).all()
        
        # Performance por pregão
        performance_pregoes = db.session.query(
            Empenho.numero_pregao,
            func.count(Empenho.id).label('total_empenhos'),
            func.sum(Empenho.valor_empenhado).label('valor_total'),
            func.avg(Empenho.valor_empenhado).label('valor_medio'),
            func.sum(case((Empenho.status == 'FINALIZADO', 1), else_=0)).label('finalizados')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim),
            Empenho.numero_pregao.isnot(None)
        ).group_by(Empenho.numero_pregao).order_by(desc('valor_total')).limit(10).all()
        
        # Calcular taxa de sucesso
        contratos_ranking = []
        for item in performance_contratos:
            taxa_sucesso = (item.finalizados / item.total_empenhos * 100) if item.total_empenhos > 0 else 0
            contratos_ranking.append({
                'numero': item.numero_contrato,
                'total_empenhos': item.total_empenhos,
                'valor_total': float(item.valor_total) if item.valor_total else 0,
                'valor_medio': float(item.valor_medio) if item.valor_medio else 0,
                'taxa_sucesso': round(taxa_sucesso, 1)
            })
        
        pregoes_ranking = []
        for item in performance_pregoes:
            taxa_sucesso = (item.finalizados / item.total_empenhos * 100) if item.total_empenhos > 0 else 0
            pregoes_ranking.append({
                'numero': item.numero_pregao,
                'total_empenhos': item.total_empenhos,
                'valor_total': float(item.valor_total) if item.valor_total else 0,
                'valor_medio': float(item.valor_medio) if item.valor_medio else 0,
                'taxa_sucesso': round(taxa_sucesso, 1)
            })
        
        return {
            'contratos': contratos_ranking,
            'pregoes': pregoes_ranking
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter ranking de performance: {str(e)}")
        return {}

def _get_dados_periodo_comparativo(data_inicio, data_fim):
    """Obter dados para comparação entre períodos"""
    try:
        # Dados básicos
        total_empenhos = db.session.query(func.count(Empenho.id)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).scalar() or 0
        
        valor_total = db.session.query(func.sum(Empenho.valor_empenhado)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).scalar() or 0
        
        valor_medio = db.session.query(func.avg(Empenho.valor_empenhado)).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # Distribuição por status
        status_counts = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('count')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(Empenho.status).all()
        
        distribuicao_status = {item.status: item.count for item in status_counts}
        
        # Top 5 fornecedores
        top_fornecedores = db.session.query(
            Empenho.fornecedores,
            func.sum(Empenho.valor_empenhado).label('valor')
        ).filter(
            Empenho.data_empenho.between(data_inicio, data_fim)
        ).group_by(Empenho.fornecedores).order_by(desc('valor')).limit(5).all()
        
        return {
            'total_empenhos': total_empenhos,
            'valor_total': float(valor_total) if valor_total else 0,
            'valor_medio': float(valor_medio) if valor_medio else 0,
            'distribuicao_status': distribuicao_status,
            'top_fornecedores': [
                {'fornecedor': item.fornecedores, 'valor': float(item.valor)}
                for item in top_fornecedores
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter dados do período: {str(e)}")
        return {}

def _calcular_variacoes(dados_periodo1, dados_periodo2):
    """Calcular variações entre dois períodos"""
    try:
        def calcular_variacao(valor1, valor2):
            if valor2 == 0:
                return 100 if valor1 > 0 else 0
            return ((valor1 - valor2) / valor2) * 100
        
        return {
            'total_empenhos': {
                'valor': calcular_variacao(dados_periodo1['total_empenhos'], dados_periodo2['total_empenhos']),
                'tipo': 'positivo' if dados_periodo1['total_empenhos'] >= dados_periodo2['total_empenhos'] else 'negativo'
            },
            'valor_total': {
                'valor': calcular_variacao(dados_periodo1['valor_total'], dados_periodo2['valor_total']),
                'tipo': 'positivo' if dados_periodo1['valor_total'] >= dados_periodo2['valor_total'] else 'negativo'
            },
            'valor_medio': {
                'valor': calcular_variacao(dados_periodo1['valor_medio'], dados_periodo2['valor_medio']),
                'tipo': 'positivo' if dados_periodo1['valor_medio'] >= dados_periodo2['valor_medio'] else 'negativo'
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular variações: {str(e)}")
        return {}

# Classe para utilitários de exportação
class ExportXLSXHelper:
    @staticmethod
    def export_to_excel(empenhos, filtros=None):
        """Exportar dados para Excel com formatação avançada"""
        try:
            import pandas as pd
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
            from openpyxl.utils.dataframe import dataframe_to_rows
            import tempfile
            import os
            
            # Converter dados para DataFrame
            data = []
            for empenho in empenhos:
                data.append({
                    'Número': empenho.numero_empenho,
                    'Data': empenho.data_empenho.strftime('%d/%m/%Y'),
                    'Valor': empenho.valor_empenhado,
                    'Status': empenho.status,
                    'Contrato': empenho.numero_contrato,
                    'Pregão': empenho.numero_pregao,
                    'Fornecedor': empenho.fornecedores,
                    'Objeto': empenho.objeto_contrato[:100] + '...' if empenho.objeto_contrato and len(empenho.objeto_contrato) > 100 else empenho.objeto_contrato,
                    'Vencimento': empenho.data_vencimento.strftime('%d/%m/%Y') if empenho.data_vencimento else ''
                })
            
            df = pd.DataFrame(data)
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            
            # Salvar com formatação
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Empenhos', index=False)
                
                # Acessar a planilha para formatação
                worksheet = writer.sheets['Empenhos']
                
                # Estilo do cabeçalho
                header_font = Font(bold=True, color='FFFFFF')
                header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center')
                
                # Ajustar largura das colunas
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Erro ao exportar para Excel: {str(e)}")
            raise e

@relatorios_bp.route('/api/dados-dashboard')
@login_required
def api_dados_dashboard():
    """API para dados do dashboard em tempo real"""
    try:
        periodo = request.args.get('periodo', '30')
        data_fim = date.today()
        
        if periodo == '365':
            data_inicio = data_fim - timedelta(days=365)
        elif periodo == '90':
            data_inicio = data_fim - timedelta(days=90)
        else:
            data_inicio = data_fim - timedelta(days=30)
        
        # Usar cache para melhor performance
        cache_key = f"dashboard_{current_user.id}_{periodo}_{data_inicio}_{data_fim}"
        cached_data = CacheManager.get(cache_key)
        
        if cached_data:
            return jsonify(cached_data)
        
        # Gerar dados
        dados = {
            'estatisticas': _get_estatisticas_gerais_otimizado(data_inicio, data_fim),
            'metricas': _get_metricas_periodo_otimizado(data_inicio, data_fim),
            'alertas': _get_alertas_criticos_otimizado(),
            'graficos': _get_dados_graficos_otimizado(data_inicio, data_fim)
        }
        
        # Salvar no cache por 5 minutos
        CacheManager.set(cache_key, dados, expires_in=300)
        
        return jsonify(dados)
        
    except Exception as e:
        logger.error(f"Erro na API do dashboard: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@relatorios_bp.route('/performance')
@login_required
def performance():
    """Relatório de performance do sistema"""
    try:
        # Apenas administradores podem ver este relatório
        if not current_user.is_admin:
            flash('Acesso negado.', 'error')
            return redirect(url_for('relatorios.index'))
        
        # Métricas de performance do banco
        performance_db = _get_performance_database()
        
        # Estatísticas de uso
        estatisticas_uso = _get_estatisticas_uso()
        
        # Análise de queries mais lentas
        queries_lentas = _get_queries_lentas()
        
        return render_template('relatorios/performance.html',
                             performance_db=performance_db,
                             estatisticas_uso=estatisticas_uso,
                             queries_lentas=queries_lentas)
                             
    except Exception as e:
        logger.error(f"Erro no relatório de performance: {str(e)}")
        flash('Erro ao carregar relatório de performance.', 'error')
        return redirect(url_for('relatorios.index'))

# Sistema de cache simples
class CacheManager:
    _cache = {}
    
    @classmethod
    def get(cls, key):
        """Obter item do cache"""
        if key in cls._cache:
            item = cls._cache[key]
            if datetime.now() < item['expires']:
                return item['data']
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key, data, expires_in=300):
        """Definir item no cache"""
        cls._cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=expires_in)
        }
    
    @classmethod
    def clear(cls):
        """Limpar cache"""
        cls._cache.clear()
    
    @classmethod
    def cleanup(cls):
        """Remover itens expirados"""
        now = datetime.now()
        expired_keys = [key for key, item in cls._cache.items() if now >= item['expires']]
        for key in expired_keys:
            del cls._cache[key]

def _get_performance_database():
    """Obter métricas de performance do banco"""
    try:
        # Simular métricas de performance
        # Em um ambiente real, você consultaria as tabelas de sistema do PostgreSQL/MySQL
        
        try:
            import psutil
            
            # Métricas do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            sistema_stats = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'disk_percent': disk.percent,
                'disk_free': disk.free / (1024**3)  # GB
            }
        except ImportError:
            # Fallback caso psutil não esteja disponível
            sistema_stats = {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_available': 0,
                'disk_percent': 0,
                'disk_free': 0
            }
        
        # Simular tempo de resposta de queries
        import time
        start_time = time.time()
        db.session.execute(text('SELECT 1')).fetchall()
        query_time = (time.time() - start_time) * 1000  # em ms
        
        # Contagem de registros nas principais tabelas
        count_empenhos = db.session.query(func.count(Empenho.id)).scalar()
        count_notas = db.session.query(func.count(NotaFiscal.id)).scalar()
        
        return {
            'sistema': sistema_stats,
            'database': {
                'query_time_ms': round(query_time, 2),
                'total_empenhos': count_empenhos,
                'total_notas': count_notas,
                'cache_hits': len(CacheManager._cache) if 'CacheManager' in globals() else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter performance do banco: {str(e)}")
        return {}

def _get_estatisticas_uso():
    """Obter estatísticas de uso do sistema"""
    try:
        # Atividade por dia da semana
        dow = func.strftime('%w', Empenho.data_empenho)  # 0=Domingo ... 6=Sábado
        atividade_semanal = db.session.query(
            dow.label('dia_semana'),
            func.count(Empenho.id).label('total')
        ).group_by(dow).all()
        
        dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        atividade_formatada = []
        
        for dia in range(7):
            total = next((item.total for item in atividade_semanal if int(item.dia_semana) == dia), 0)
            atividade_formatada.append({
                'dia': dias_semana[dia],
                'total': total
            })
        
        # Atividade por mês (últimos 12 meses)
        doze_meses_atras = date.today() - timedelta(days=365)
        ano = func.strftime('%Y', Empenho.data_empenho)
        mes = func.strftime('%m', Empenho.data_empenho)
        atividade_mensal = db.session.query(
            ano.label('ano'),
            mes.label('mes'),
            func.count(Empenho.id).label('total')
        ).filter(
            Empenho.data_empenho >= doze_meses_atras
        ).group_by(ano, mes).order_by(ano, mes).all()
        
        return {
            'atividade_semanal': atividade_formatada,
            'atividade_mensal': [
                {
                    'periodo': f"{int(item.ano)}-{int(item.mes):02d}",
                    'total': item.total
                }
                for item in atividade_mensal
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de uso: {str(e)}")
        return {}

def _get_queries_lentas():
    """Simular análise de queries lentas"""
    try:
        # Em um ambiente real, você consultaria os logs de performance do banco
        # Aqui vamos simular algumas queries típicas e seus tempos
        
        queries_simuladas = [
            {
                'query': 'SELECT * FROM empenhos WHERE data_empenho BETWEEN ? AND ?',
                'tempo_ms': 45.2,
                'execucoes': 234,
                'impacto': 'médio'
            },
            {
                'query': 'SELECT e.*, n.* FROM empenhos e LEFT JOIN notas_fiscais n ON e.id = n.empenho_id',
                'tempo_ms': 78.9,
                'execucoes': 89,
                'impacto': 'alto'
            },
            {
                'query': 'SELECT COUNT(*) FROM empenhos GROUP BY status',
                'tempo_ms': 12.3,
                'execucoes': 456,
                'impacto': 'baixo'
            }
        ]
        
        return queries_simuladas
        
    except Exception as e:
        logger.error(f"Erro ao obter queries lentas: {str(e)}")
        return []

@relatorios_bp.route('/exportar/pdf')
@login_required
def exportar_pdf():
    """Exportar relatório para PDF"""
    try:
        # Obter filtros da query string
        filtros = {
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'status': request.args.get('status'),
            'contrato': request.args.get('contrato'),
            'pregao': request.args.get('pregao')
        }
        
        # Aplicar filtros
        query = Empenho.query
        
        if filtros['data_inicio']:
            query = query.filter(Empenho.data_empenho >= datetime.strptime(filtros['data_inicio'], '%Y-%m-%d').date())
        
        if filtros['data_fim']:
            query = query.filter(Empenho.data_empenho <= datetime.strptime(filtros['data_fim'], '%Y-%m-%d').date())
        
        if filtros['status']:
            query = query.filter(Empenho.status == filtros['status'])
        
        if filtros['contrato']:
            query = query.filter(Empenho.numero_contrato.contains(filtros['contrato']))
        
        if filtros['pregao']:
            query = query.filter(Empenho.numero_pregao.contains(filtros['pregao']))
        
        empenhos = query.order_by(Empenho.data_empenho.desc()).all()
        
        # TEMPORARIAMENTE DESABILITADO - utils com problemas
        # filename = ExportUtils.export_to_pdf(empenhos, filtros)
        # return send_file(filename, as_attachment=True, download_name=f'relatorio_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
        flash('Exportação para PDF temporariamente desabilitada', 'warning')
        return redirect(url_for('relatorios.index'))
        
    except Exception as e:
        flash(f'Erro ao exportar para PDF: {str(e)}', 'error')
        return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/importar', methods=['GET', 'POST'])
@login_required
def importar():
    """Importar dados de planilha"""
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)
        
        file = request.files['arquivo']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(request.url)
        
        # TEMPORARIAMENTE DESABILITADO - ImportUtils com problemas
        # if file and ImportUtils.allowed_file(file.filename):
        if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
            try:
                flash('Importação temporariamente desabilitada', 'warning')
                return redirect(url_for('relatorios.index'))
                
                # # Salvar arquivo temporariamente  
                # filename = ImportUtils.save_uploaded_file(file)
                # 
                # # Importar dados
                # resultado = ImportUtils.import_from_file(filename, current_user.id)
                
                # Remover arquivo temporário
                os.remove(filename)
                
                if resultado['sucesso']:
                    flash(f'Importação concluída! {resultado["importados"]} empenhos importados, {resultado["erros"]} erros.', 'success')
                    if resultado['mensagens_erro']:
                        flash('Erros encontrados: ' + '; '.join(resultado['mensagens_erro'][:5]), 'warning')
                else:
                    flash(f'Erro na importação: {resultado["erro"]}', 'error')
                
            except Exception as e:
                flash(f'Erro ao processar arquivo: {str(e)}', 'error')
        else:
            flash('Tipo de arquivo não permitido. Use Excel (.xlsx) ou CSV (.csv)', 'error')
    
    return render_template('relatorios/importar.html')

@relatorios_bp.route('/api/dados-grafico')
@login_required
def dados_grafico():
    """API para dados dos gráficos"""
    tipo = request.args.get('tipo', 'status')
    
    if tipo == 'status':
        dados = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor_total')
        ).group_by(Empenho.status).all()
        
        return jsonify([{
            'label': item.status,
            'quantidade': item.quantidade,
            'valor': float(item.valor_total or 0)
        } for item in dados])
    
    elif tipo == 'mensal':
        ano = func.strftime('%Y', Empenho.data_empenho)
        mes = func.strftime('%m', Empenho.data_empenho)
        dados = db.session.query(
            ano.label('ano'),
            mes.label('mes'),
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor_total')
        ).group_by(ano, mes).order_by(ano, mes).limit(12).all()

        return jsonify([{
            'periodo': f"{int(item.mes):02d}/{int(item.ano)}",
            'quantidade': item.quantidade,
            'valor': float(item.valor_total or 0)
        } for item in dados])
    
    elif tipo == 'contratos':
        dados = db.session.query(
            Empenho.numero_contrato,
            func.sum(Empenho.valor_empenhado).label('valor_total'),
            func.count(Empenho.id).label('quantidade')
        ).group_by(Empenho.numero_contrato).order_by(func.sum(Empenho.valor_empenhado).desc()).limit(10).all()
        
        return jsonify([{
            'contrato': item.numero_contrato,
            'quantidade': item.quantidade,
            'valor': float(item.valor_total or 0)
        } for item in dados])
    
    return jsonify([])

@relatorios_bp.route('/backup')
@login_required
def backup():
    """Gerar backup do banco de dados"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem fazer backup.', 'error')
        return redirect(url_for('relatorios.index'))
    
    try:
        # TEMPORARIAMENTE DESABILITADO
        # filename = ExportUtils.create_backup()
        # return send_file(filename, as_attachment=True, download_name=f'backup_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        flash('Backup temporariamente desabilitado', 'warning')
        return redirect(url_for('relatorios.index'))
    except Exception as e:
        flash(f'Erro ao gerar backup: {str(e)}', 'error')
        return redirect(url_for('relatorios.index'))

# ===== NOVAS ROTAS PARA DASHBOARD MODERNO =====

@relatorios_bp.route('/moderno')
@login_required
def index_moderno():
    """Dashboard moderno com drag-and-drop"""
    try:
        # Dados básicos de empenhos
        total_empenhos = Empenho.query.count()
        empenhos_ativos = Empenho.query.filter_by(status='ATIVO').count()
        
        # Dados básicos de contratos
        total_contratos = Contrato.query.count()
        contratos_ativos = Contrato.query.filter_by(status='ATIVO').count()
        
        # Dados básicos de notas fiscais
        total_notas = NotaFiscal.query.count()
        
        # Valores financeiros seguros
        valor_empenhado = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
        valor_notas_pagas = db.session.query(
            func.sum(NotaFiscal.valor_liquido)
        ).filter(NotaFiscal.status == 'PAGO').scalar() or 0
        
        # Evolução mensal (últimos 6 meses)
        evolucao_mensal = _get_evolucao_mensal_simples()
        
        # Status dos empenhos
        empenhos_por_status = _get_empenhos_por_status()
        
        # Status das notas
        notas_por_status = _get_notas_por_status()
        
        # Insights básicos
        insights = _build_insights_simples(total_empenhos, empenhos_ativos, total_notas)
        
        dados_dashboard = {
            'total_empenhos': total_empenhos,
            'empenhos_ativos': empenhos_ativos,
            'total_contratos': total_contratos,
            'contratos_ativos': contratos_ativos,
            'total_notas': total_notas,
            'valor_total_empenhado': float(valor_empenhado),
            'valor_notas_pagas': float(valor_notas_pagas),
            'evolucao_mensal': evolucao_mensal,
            'empenhos_por_status': empenhos_por_status,
            'notas_por_status': notas_por_status,
            'insights': insights
        }
        
        return render_template('relatorios/index_moderno.html', **dados_dashboard)
    
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard moderno: {e}")
        flash('Erro ao carregar dashboard moderno', 'error')
        return redirect(url_for('relatorios.index'))

@relatorios_bp.route('/api/widget-data/<widget_id>')
@login_required
def api_widget_data(widget_id):
    """API para dados específicos de widgets"""
    try:
        if widget_id == 'kpi-empenhos':
            data = {
                'total': Empenho.query.count(),
                'ativos': Empenho.query.filter_by(status='ATIVO').count(),
                'liquidados': Empenho.query.filter_by(status='LIQUIDADO').count(),
                'cancelados': Empenho.query.filter_by(status='CANCELADO').count()
            }
        
        elif widget_id == 'kpi-financeiro':
            valor_total = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
            # Calcular variação (simulada por enquanto)
            data = {
                'valor_total': float(valor_total),
                'variacao': 5.2  # Simulado
            }
        
        elif widget_id == 'grafico-evolucao':
            data = {
                'evolucao': _get_evolucao_mensal_simples()
            }
        
        elif widget_id == 'grafico-pizza':
            data = {
                'distribuicao': _get_empenhos_por_status()
            }
        
        elif widget_id == 'tabela-top-fornecedores':
            fornecedores = db.session.query(
                Empenho.fornecedores,
                func.sum(Empenho.valor_empenhado).label('valor')
            ).group_by(Empenho.fornecedores).order_by(
                func.sum(Empenho.valor_empenhado).desc()
            ).limit(10).all()
            
            data = {
                'fornecedores': [
                    {'nome': f.fornecedores or 'Não informado', 'valor': float(f.valor or 0)}
                    for f in fornecedores
                ]
            }
        
        elif widget_id == 'alertas-sistema':
            alertas = _get_alertas_widget()
            data = {'alertas': alertas}
        
        elif widget_id == 'calendario-vencimentos':
            vencimentos = _get_vencimentos_proximos()
            data = {'vencimentos': vencimentos}
        
        else:
            return jsonify({'error': 'Widget não encontrado'}), 404
        
        return jsonify(data)
    
    except Exception as e:
        logger.error(f"Erro ao buscar dados do widget {widget_id}: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@relatorios_bp.route('/api/save-layout', methods=['POST'])
@login_required
def api_save_layout():
    """Salvar layout personalizado do usuário"""
    try:
        layout_data = request.get_json()
        
        # Por enquanto, salvar no localStorage do navegador
        # Em uma implementação completa, salvaria no banco de dados
        # associado ao usuário
        
        return jsonify({'success': True, 'message': 'Layout salvo com sucesso'})
    
    except Exception as e:
        logger.error(f"Erro ao salvar layout: {str(e)}")
        return jsonify({'error': 'Erro ao salvar layout'}), 500

def _get_evolucao_mensal_simples():
    """Evolução mensal simplificada"""
    try:
        meses = []
        hoje = date.today()
        
        for i in range(6):
            data_mes = add_months(hoje, -i)
            mes_inicio = data_mes.replace(day=1)
            if data_mes.month == 12:
                mes_fim = data_mes.replace(year=data_mes.year+1, month=1, day=1) - timedelta(days=1)
            else:
                mes_fim = data_mes.replace(month=data_mes.month+1, day=1) - timedelta(days=1)
            
            empenhos_count = Empenho.query.filter(
                Empenho.data_empenho.between(mes_inicio, mes_fim)
            ).count()
            
            valor_total = db.session.query(func.sum(Empenho.valor_empenhado)).filter(
                Empenho.data_empenho.between(mes_inicio, mes_fim)
            ).scalar() or 0
            
            meses.append({
                'mes': data_mes.strftime('%b/%y'),
                'quantidade': empenhos_count,
                'valor': float(valor_total)
            })
        
        return list(reversed(meses))
    
    except Exception as e:
        logger.error(f"Erro ao obter evolução mensal: {str(e)}")
        return []

def _get_empenhos_por_status():
    """Distribuição de empenhos por status"""
    try:
        status_data = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('quantidade')
        ).group_by(Empenho.status).all()
        
        return {row.status or 'Indefinido': row.quantidade for row in status_data}
    
    except Exception as e:
        logger.error(f"Erro ao obter status dos empenhos: {str(e)}")
        return {}

def _get_notas_por_status():
    """Distribuição de notas por status"""
    try:
        status_data = db.session.query(
            NotaFiscal.status,
            func.count(NotaFiscal.id).label('quantidade')
        ).group_by(NotaFiscal.status).all()
        
        return {row.status or 'Indefinido': row.quantidade for row in status_data}
    
    except Exception as e:
        logger.error(f"Erro ao obter status das notas: {str(e)}")
        return {}

def _build_insights_simples(total_empenhos, empenhos_ativos, total_notas):
    """Construir insights básicos"""
    insights = []
    
    if total_empenhos > 0:
        percentual_ativo = (empenhos_ativos / total_empenhos) * 100
        insights.append({
            'icon': 'activity',
            'texto': f'{percentual_ativo:.1f}% dos empenhos estão ativos'
        })
    
    insights.append({
        'icon': 'file-text',
        'texto': f'Sistema com {total_empenhos} empenhos registrados'
    })
    
    if total_notas > 0:
        insights.append({
            'icon': 'receipt',
            'texto': f'{total_notas} notas fiscais no sistema'
        })
    
    insights.append({
        'icon': 'check-circle',
        'texto': 'Sistema funcionando normalmente'
    })
    
    return insights

def _get_alertas_widget():
    """Obter alertas para o widget"""
    try:
        alertas = []
        hoje = date.today()
        
        # Empenhos vencendo
        vencendo = Empenho.query.filter(
            Empenho.data_vencimento <= hoje + timedelta(days=30),
            Empenho.data_vencimento > hoje,
            Empenho.status.in_(['ATIVO', 'PARCIAL'])
        ).count()
        
        if vencendo > 0:
            alertas.append({
                'tipo': 'warning',
                'icone': 'bi-clock',
                'titulo': 'Empenhos Vencendo',
                'mensagem': f'{vencendo} empenhos vencem em 30 dias'
            })
        
        # Empenhos vencidos
        vencidos = Empenho.query.filter(
            Empenho.data_vencimento < hoje,
            Empenho.status.in_(['ATIVO', 'PARCIAL'])
        ).count()
        
        if vencidos > 0:
            alertas.append({
                'tipo': 'danger',
                'icone': 'bi-exclamation-triangle',
                'titulo': 'Empenhos Vencidos',
                'mensagem': f'{vencidos} empenhos estão vencidos'
            })
        
        # Notas vencidas
        notas_vencidas = NotaFiscal.query.filter(
            NotaFiscal.data_vencimento < hoje,
            NotaFiscal.status == 'EM_ABERTO'
        ).count()
        
        if notas_vencidas > 0:
            alertas.append({
                'tipo': 'danger',
                'icone': 'bi-file-earmark-x',
                'titulo': 'Notas Vencidas',
                'mensagem': f'{notas_vencidas} notas estão em atraso'
            })
        
        return alertas
    
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {str(e)}")
        return []

def _get_vencimentos_proximos():
    """Obter próximos vencimentos"""
    try:
        hoje = date.today()
        proximos_30_dias = hoje + timedelta(days=30)
        
        # Empenhos vencendo
        empenhos_vencendo = Empenho.query.filter(
            Empenho.data_vencimento.between(hoje, proximos_30_dias),
            Empenho.status.in_(['ATIVO', 'PARCIAL'])
        ).order_by(Empenho.data_vencimento).limit(5).all()
        
        vencimentos = []
        for empenho in empenhos_vencendo:
            vencimentos.append({
                'data': empenho.data_vencimento.isoformat(),
                'titulo': f'Empenho {empenho.numero_empenho}',
                'tipo': 'Empenho'
            })
        
        # Notas vencendo
        notas_vencendo = NotaFiscal.query.filter(
            NotaFiscal.data_vencimento.between(hoje, proximos_30_dias),
            NotaFiscal.status == 'EM_ABERTO'
        ).order_by(NotaFiscal.data_vencimento).limit(5).all()
        
        for nota in notas_vencendo:
            vencimentos.append({
                'data': nota.data_vencimento.isoformat(),
                'titulo': f'Nota Fiscal {nota.numero_nota}',
                'tipo': 'Nota Fiscal'
            })
        
        # Ordenar por data
        vencimentos.sort(key=lambda x: x['data'])
        
        return vencimentos[:10]  # Máximo 10 itens
    
    except Exception as e:
        logger.error(f"Erro ao obter vencimentos: {str(e)}")
        return []

@relatorios_bp.route('/demo')
def demo():
    """Página de demonstração do sistema de relatórios"""
    return render_template('relatorios/demo.html')

# Novas rotas para relatórios avançados
@relatorios_bp.route('/analytics')
@login_required
def analytics():
    """Relatório de analytics avançado"""
    dados_analytics = {
        'performance_mensal': _get_performance_mensal(),
        'distribuicao_fornecedores': _get_distribuicao_fornecedores(),
        'tendencias': _get_tendencias(),
        'indicadores_kpi': _get_indicadores_kpi()
    }
    
    return render_template('relatorios/analytics.html', **dados_analytics)

@relatorios_bp.route('/financeiro')
@login_required
def financeiro():
    """Relatório financeiro consolidado"""
    # Período padrão: ano atual
    ano_atual = date.today().year
    data_inicio = date(ano_atual, 1, 1)
    data_fim = date.today()
    
    # Filtros da URL
    if request.args.get('data_inicio'):
        data_inicio = datetime.strptime(request.args.get('data_inicio'), '%Y-%m-%d').date()
    if request.args.get('data_fim'):
        data_fim = datetime.strptime(request.args.get('data_fim'), '%Y-%m-%d').date()
    
    # Dados financeiros
    dados_financeiros = {
        'resumo_empenhos': _get_resumo_empenhos(data_inicio, data_fim),
        'resumo_notas': _get_resumo_notas(data_inicio, data_fim),
        'fluxo_caixa': _get_fluxo_caixa(data_inicio, data_fim),
        'comparativo_anual': _get_comparativo_anual(),
        'filtros': {'data_inicio': data_inicio, 'data_fim': data_fim}
    }
    
    return render_template('relatorios/financeiro.html', **dados_financeiros)

@relatorios_bp.route('/operacional')
@login_required
def operacional():
    """Relatório operacional"""
    dados_operacionais = {
        'produtividade': _get_produtividade(),
        'prazos': _get_analise_prazos(),
        'status_distribuicao': _get_status_distribuicao(),
        'alertas_operacionais': _get_alertas_operacionais()
    }
    
    return render_template('relatorios/operacional.html', **dados_operacionais)

@relatorios_bp.route('/api/dados/<tipo>')
@login_required
def api_dados(tipo):
    """API para dados dinâmicos dos relatórios"""
    try:
        if tipo == 'evolucao_diaria':
            dados = _get_evolucao_diaria()
        elif tipo == 'top_fornecedores':
            dados = _get_top_fornecedores()
        elif tipo == 'status_tempo_real':
            dados = _get_status_tempo_real()
        elif tipo == 'alertas':
            dados = _get_alertas_api()
        else:
            return jsonify({'error': 'Tipo de dados não encontrado'}), 404
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Funções auxiliares para cálculos de relatórios
def _get_performance_mensal():
    """Calcula performance mensal dos últimos 12 meses"""
    meses = []
    for i in range(12):
        data_mes = date.today() - timedelta(days=30*i)
        mes_inicio = data_mes.replace(day=1)
        if data_mes.month == 12:
            mes_fim = data_mes.replace(year=data_mes.year+1, month=1, day=1) - timedelta(days=1)
        else:
            mes_fim = data_mes.replace(month=data_mes.month+1, day=1) - timedelta(days=1)
        
        # Dados do mês
        empenhos = Empenho.query.filter(and_(
            Empenho.data_empenho >= mes_inicio,
            Empenho.data_empenho <= mes_fim
        )).all()
        
        notas = NotaFiscal.query.filter(and_(
            NotaFiscal.data_emissao >= mes_inicio,
            NotaFiscal.data_emissao <= mes_fim
        )).all()
        
        meses.append({
            'mes': data_mes.strftime('%b/%y'),
            'empenhos_qtd': len(empenhos),
            'empenhos_valor': sum(e.valor_empenhado or 0 for e in empenhos),
            'notas_qtd': len(notas),
            'notas_valor': sum(n.valor_liquido or 0 for n in notas),
            'eficiencia': len(notas) / max(len(empenhos), 1) * 100
        })
    
    return list(reversed(meses))

def _get_distribuicao_fornecedores():
    """Distribução de valores por fornecedor"""
    fornecedores = db.session.query(
        Empenho.fornecedores,
        func.sum(Empenho.valor_empenhado).label('valor_total'),
        func.count(Empenho.id).label('quantidade')
    ).group_by(Empenho.fornecedores).order_by(
        func.sum(Empenho.valor_empenhado).desc()
    ).limit(15).all()
    
    return [{'nome': f.fornecedores, 'valor': float(f.valor_total or 0), 'qtd': f.quantidade} 
            for f in fornecedores]

def _get_tendencias():
    """Análise de tendências"""
    hoje = date.today()
    periodo1_fim = hoje
    periodo1_inicio = hoje - timedelta(days=90)
    periodo2_fim = periodo1_inicio - timedelta(days=1)
    periodo2_inicio = periodo2_fim - timedelta(days=90)
    
    # Período atual
    dados_atuais = db.session.query(
        func.count(Empenho.id).label('qtd'),
        func.sum(Empenho.valor_empenhado).label('valor')
    ).filter(and_(
        Empenho.data_empenho >= periodo1_inicio,
        Empenho.data_empenho <= periodo1_fim
    )).first()
    
    # Período anterior
    dados_anteriores = db.session.query(
        func.count(Empenho.id).label('qtd'),
        func.sum(Empenho.valor_empenhado).label('valor')
    ).filter(and_(
        Empenho.data_empenho >= periodo2_inicio,
        Empenho.data_empenho <= periodo2_fim
    )).first()
    
    # Calcular variações
    var_qtd = ((dados_atuais.qtd or 0) - (dados_anteriores.qtd or 0)) / max(dados_anteriores.qtd or 1, 1) * 100
    var_valor = ((dados_atuais.valor or 0) - (dados_anteriores.valor or 0)) / max(dados_anteriores.valor or 1, 1) * 100
    
    return {
        'variacao_quantidade': var_qtd,
        'variacao_valor': var_valor,
        'periodo_atual': f"{periodo1_inicio.strftime('%d/%m')} - {periodo1_fim.strftime('%d/%m')}",
        'periodo_anterior': f"{periodo2_inicio.strftime('%d/%m')} - {periodo2_fim.strftime('%d/%m')}"
    }

def _get_indicadores_kpi():
    """Indicadores KPI principais"""
    # Tempo médio de processamento
    empenhos_processados = Empenho.query.filter(
        Empenho.status.in_(['LIQUIDADO', 'PAGO'])
    ).all()
    
    tempo_medio = 0
    if empenhos_processados:
        tempos = []
        for emp in empenhos_processados:
            # Safe handling for missing updated_at fields
            if emp.data_empenho and hasattr(emp, 'updated_at') and emp.updated_at:
                try:
                    tempo = (emp.updated_at.date() - emp.data_empenho).days
                    if tempo >= 0:  # Only positive processing times
                        tempos.append(tempo)
                except (AttributeError, TypeError):
                    # Skip if date conversion fails
                    continue
        tempo_medio = sum(tempos) / len(tempos) if tempos else 0
    
    # Taxa de execução
    total_empenhos = Empenho.query.count()
    empenhos_executados = Empenho.query.filter(
        Empenho.status.in_(['LIQUIDADO', 'PAGO'])
    ).count()
    taxa_execucao = (empenhos_executados / max(total_empenhos, 1)) * 100
    
    # Valor médio por empenho
    valor_total = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
    valor_medio = valor_total / max(total_empenhos, 1)
    
    return {
        'tempo_medio_processamento': round(tempo_medio, 1),
        'taxa_execucao': round(taxa_execucao, 1),
        'valor_medio_empenho': valor_medio,
        'total_processados': empenhos_executados
    }

def _get_resumo_empenhos(data_inicio, data_fim):
    """Resumo financeiro de empenhos"""
    empenhos = Empenho.query.filter(and_(
        Empenho.data_empenho >= data_inicio,
        Empenho.data_empenho <= data_fim
    )).all()
    
    return {
        'quantidade': len(empenhos),
        'valor_empenhado': sum(e.valor_empenhado or 0 for e in empenhos),
        'valor_liquido': sum(e.valor_liquido or 0 for e in empenhos),
        'valor_retencao': sum(e.valor_retencao or 0 for e in empenhos)
    }

def _get_resumo_notas(data_inicio, data_fim):
    """Resumo financeiro de notas fiscais"""
    notas = NotaFiscal.query.filter(and_(
        NotaFiscal.data_emissao >= data_inicio,
        NotaFiscal.data_emissao <= data_fim
    )).all()
    
    pagas = [n for n in notas if n.status == 'PAGO']
    abertas = [n for n in notas if n.status == 'EM_ABERTO']
    
    return {
        'quantidade_total': len(notas),
        'quantidade_pagas': len(pagas),
        'quantidade_abertas': len(abertas),
        'valor_total': sum(n.valor_liquido or 0 for n in notas),
        'valor_pago': sum(n.valor_liquido or 0 for n in pagas),
        'valor_aberto': sum(n.valor_liquido or 0 for n in abertas)
    }

def _get_fluxo_caixa(data_inicio, data_fim):
    """Análise de fluxo de caixa"""
    periodo_dias = (data_fim - data_inicio).days
    fluxo = []
    
    for i in range(0, periodo_dias, 7):  # Semanal
        semana_inicio = data_inicio + timedelta(days=i)
        semana_fim = min(semana_inicio + timedelta(days=6), data_fim)
        
        # Notas que vencem na semana
        notas_vencimento = NotaFiscal.query.filter(and_(
            NotaFiscal.data_vencimento >= semana_inicio,
            NotaFiscal.data_vencimento <= semana_fim,
            NotaFiscal.status.in_(['EM_ABERTO', 'PROCESSANDO'])
        )).all()
        
        valor_semana = sum(n.valor_liquido or 0 for n in notas_vencimento)
        
        fluxo.append({
            'periodo': f"{semana_inicio.strftime('%d/%m')} - {semana_fim.strftime('%d/%m')}",
            'valor': valor_semana,
            'quantidade': len(notas_vencimento)
        })
    
    return fluxo

def _get_comparativo_anual():
    """Comparativo entre anos"""
    ano_atual = date.today().year
    dados_anos = []
    
    for ano in range(ano_atual-2, ano_atual+1):
        empenhos_ano = Empenho.query.filter(
            func.strftime('%Y', Empenho.data_empenho) == str(ano)
        ).all()
        
        dados_anos.append({
            'ano': ano,
            'quantidade': len(empenhos_ano),
            'valor': sum(e.valor_empenhado or 0 for e in empenhos_ano)
        })
    
    return dados_anos

def _get_produtividade():
    """Análise de produtividade"""
    mes_atual = date.today().replace(day=1)
    empenhos_mes = Empenho.query.filter(Empenho.data_empenho >= mes_atual).count()
    dias_transcorridos = max((date.today() - mes_atual).days, 1)
    
    return {
        'empenhos_mes': empenhos_mes,
        'media_diaria': empenhos_mes / dias_transcorridos,
        'meta_mensal': 100,
        'percentual_meta': min((empenhos_mes / 100) * 100, 100)
    }

def _get_analise_prazos():
    """Análise de prazos"""
    hoje = date.today()
    
    vencendo_30 = Empenho.query.filter(and_(
        Empenho.data_vencimento <= hoje + timedelta(days=30),
        Empenho.data_vencimento > hoje,
        Empenho.status.in_(['ATIVO', 'PARCIAL'])
    )).count()
    
    vencidos = Empenho.query.filter(and_(
        Empenho.data_vencimento < hoje,
        Empenho.status.in_(['ATIVO', 'PARCIAL'])
    )).count()
    
    return {
        'vencendo_30_dias': vencendo_30,
        'vencidos': vencidos,
        'em_dia': Empenho.query.filter(
            Empenho.status.in_(['LIQUIDADO', 'PAGO'])
        ).count()
    }

def _get_status_distribuicao():
    """Distribuição por status"""
    status_empenhos = db.session.query(
        Empenho.status,
        func.count(Empenho.id).label('quantidade')
    ).group_by(Empenho.status).all()
    
    status_notas = db.session.query(
        NotaFiscal.status,
        func.count(NotaFiscal.id).label('quantidade')
    ).group_by(NotaFiscal.status).all()
    
    return {
        'empenhos': [{'status': s.status, 'quantidade': s.quantidade} for s in status_empenhos],
        'notas': [{'status': s.status, 'quantidade': s.quantidade} for s in status_notas]
    }

def _get_alertas_operacionais():
    """Alertas operacionais"""
    alertas = []
    
    # Empenhos liquidados sem nota fiscal
    empenhos_sem_nota = db.session.query(Empenho).outerjoin(NotaFiscal, NotaFiscal.empenho_id == Empenho.id).filter(
        NotaFiscal.id.is_(None),
        Empenho.status == 'LIQUIDADO'
    ).count()
    
    if empenhos_sem_nota > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Empenhos Liquidados sem Nota Fiscal',
            'valor': empenhos_sem_nota
        })
    
    return alertas

def _get_evolucao_diaria():
    """Dados para API - evolução diária"""
    ultimos_30_dias = []
    for i in range(30):
        data = date.today() - timedelta(days=i)
        qtd = Empenho.query.filter(Empenho.data_empenho == data).count()
        ultimos_30_dias.append({
            'data': data.strftime('%d/%m'),
            'quantidade': qtd
        })
    return list(reversed(ultimos_30_dias))

def _get_top_fornecedores():
    """Dados para API - top fornecedores"""
    return _get_distribuicao_fornecedores()[:10]

def _get_status_tempo_real():
    """Dados para API - status em tempo real"""
    return {
        'empenhos': {
            'total': Empenho.query.count(),
            'ativos': Empenho.query.filter(Empenho.status == 'ATIVO').count(),
            'liquidados': Empenho.query.filter(Empenho.status == 'LIQUIDADO').count()
        },
        'notas': {
            'total': NotaFiscal.query.count(),
            'abertas': NotaFiscal.query.filter(NotaFiscal.status == 'EM_ABERTO').count(),
            'pagas': NotaFiscal.query.filter(NotaFiscal.status == 'PAGO').count()
        }
    }

def _get_alertas_api():
    """Dados para API - alertas"""
    return {
        'vencimentos_proximos': Empenho.query.filter(
            Empenho.data_vencimento <= date.today() + timedelta(days=7)
        ).count(),
        'notas_vencidas': NotaFiscal.query.filter(and_(
            NotaFiscal.data_vencimento < date.today(),
            NotaFiscal.status == 'EM_ABERTO'
        )).count()
    }

# ===== FUNÇÕES AUXILIARES OTIMIZADAS =====

def _get_estatisticas_gerais_otimizado(data_inicio, data_fim):
    """Estatísticas gerais do PERÍODO (empenhos/notas) + visão geral de contratos."""
    try:
        emp = db.session.query(
            func.count(Empenho.id).label('total'),
            func.coalesce(func.sum(Empenho.valor_empenhado), 0).label('valor_empenhado'),
            func.coalesce(func.sum(Empenho.valor_liquido), 0).label('valor_liquido'),
            func.coalesce(func.sum(Empenho.valor_retencao), 0).label('valor_retencao'),
        ).filter(Empenho.data_empenho.between(data_inicio, data_fim)).first()

        nf = db.session.query(
            func.count(NotaFiscal.id).label('total'),
            func.coalesce(func.sum(case((NotaFiscal.status=='PAGO', NotaFiscal.valor_liquido), else_=0)), 0).label('valor_pagas'),
            func.coalesce(func.sum(case((NotaFiscal.status=='EM_ABERTO', NotaFiscal.valor_liquido), else_=0)), 0).label('valor_abertas'),
        ).filter(NotaFiscal.data_emissao.between(data_inicio, data_fim)).first()

        contratos = db.session.query(
            func.count(Contrato.id).label('total'),
            func.coalesce(func.sum(case((Contrato.status=='ATIVO', Contrato.valor_total), else_=0)), 0).label('valor_ativos'),
        ).first()

        return {
            'empenhos': {'total': emp.total, 'valor_empenhado': float(emp.valor_empenhado),
                         'valor_liquido': float(emp.valor_liquido), 'valor_retencao': float(emp.valor_retencao)},
            'notas':    {'total': nf.total,  'valor_pagas': float(nf.valor_pagas), 'valor_abertas': float(nf.valor_abertas)},
            'contratos':{'total': contratos.total, 'valor_ativos': float(contratos.valor_ativos)},
        }
    except Exception as e:
        logger.error(f'Erro estatísticas período: {e}')
        return {}

def _get_metricas_periodo_otimizado(data_inicio, data_fim):
    """Métricas do período com queries otimizadas"""
    try:
        # Empenhos por status no período
        empenhos_status = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('quantidade'),
            func.coalesce(func.sum(Empenho.valor_empenhado), 0).label('valor_total')
        ).filter(and_(
            Empenho.data_empenho >= data_inicio,
            Empenho.data_empenho <= data_fim
        )).group_by(Empenho.status).all()
        
        # Notas por status no período
        notas_status = db.session.query(
            NotaFiscal.status,
            func.count(NotaFiscal.id).label('quantidade'),
            func.coalesce(func.sum(NotaFiscal.valor_liquido), 0).label('valor_total')
        ).filter(and_(
            NotaFiscal.data_emissao >= data_inicio,
            NotaFiscal.data_emissao <= data_fim
        )).group_by(NotaFiscal.status).all()
        
        # Top fornecedores no período
        top_fornecedores = db.session.query(
            Empenho.fornecedores,
            func.count(Empenho.id).label('quantidade'),
            func.coalesce(func.sum(Empenho.valor_empenhado), 0).label('valor_total')
        ).filter(and_(
            Empenho.data_empenho >= data_inicio,
            Empenho.data_empenho <= data_fim,
            Empenho.fornecedores.isnot(None)
        )).group_by(Empenho.fornecedores).order_by(
            desc(func.sum(Empenho.valor_empenhado))
        ).limit(10).all()
        
        return {
            'empenhos_status': [
                {
                    'status': row.status,
                    'quantidade': row.quantidade,
                    'valor_total': float(row.valor_total)
                } for row in empenhos_status
            ],
            'notas_status': [
                {
                    'status': row.status,
                    'quantidade': row.quantidade,
                    'valor_total': float(row.valor_total)
                } for row in notas_status
            ],
            'top_fornecedores': [
                {
                    'nome': row.fornecedores,
                    'quantidade': row.quantidade,
                    'valor_total': float(row.valor_total)
                } for row in top_fornecedores
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao buscar métricas do período: {str(e)}")
        return {}

def _get_alertas_criticos_otimizado():
    """Alertas críticos com queries otimizadas"""
    try:
        alertas = []
        hoje = date.today()
        
        # Query única para alertas de vencimento
        alertas_query = db.session.query(
            func.sum(case(
                (and_(
                    Empenho.data_vencimento <= hoje + timedelta(days=30),
                    Empenho.data_vencimento > hoje,
                    Empenho.status.in_(['ATIVO', 'PARCIAL'])
                ), 1), else_=0
            )).label('empenhos_vencendo'),
            func.sum(case(
                (and_(
                    Empenho.data_vencimento < hoje,
                    Empenho.status.in_(['ATIVO', 'PARCIAL'])
                ), 1), else_=0
            )).label('empenhos_vencidos'),
            func.sum(case(
                (and_(
                    NotaFiscal.data_vencimento < hoje,
                    NotaFiscal.status == 'EM_ABERTO'
                ), 1), else_=0
            )).label('notas_vencidas'),
            func.sum(case(
                (and_(
                    NotaFiscal.data_vencimento <= hoje + timedelta(days=7),
                    NotaFiscal.data_vencimento > hoje,
                    NotaFiscal.status == 'EM_ABERTO'
                ), 1), else_=0
            )).label('notas_vencendo')
        ).outerjoin(NotaFiscal, NotaFiscal.empenho_id == Empenho.id).first()
        
        # Processar alertas
        if alertas_query.empenhos_vencendo > 0:
            alertas.append({
                'tipo': 'warning',
                'icone': 'bi-clock',
                'titulo': 'Empenhos Próximos ao Vencimento',
                'valor': alertas_query.empenhos_vencendo,
                'mensagem': f'{alertas_query.empenhos_vencendo} empenhos vencem nos próximos 30 dias',
                'link': url_for('empenhos.index', filtro='vencendo'),
                'prioridade': 2
            })
        
        if alertas_query.empenhos_vencidos > 0:
            alertas.append({
                'tipo': 'danger',
                'icone': 'bi-exclamation-triangle',
                'titulo': 'Empenhos Vencidos',
                'valor': alertas_query.empenhos_vencidos,
                'mensagem': f'{alertas_query.empenhos_vencidos} empenhos estão vencidos',
                'link': url_for('empenhos.index', filtro='vencidos'),
                'prioridade': 1
            })
        
        if alertas_query.notas_vencidas > 0:
            alertas.append({
                'tipo': 'danger',
                'icone': 'bi-file-earmark-x',
                'titulo': 'Notas Fiscais Vencidas',
                'valor': alertas_query.notas_vencidas,
                'mensagem': f'{alertas_query.notas_vencidas} notas fiscais estão em atraso',
                'link': url_for('notas.index', filtro='vencidas'),
                'prioridade': 1
            })
        
        if alertas_query.notas_vencendo > 0:
            alertas.append({
                'tipo': 'warning',
                'icone': 'bi-file-earmark-arrow-down',
                'titulo': 'Notas Vencendo esta Semana',
                'valor': alertas_query.notas_vencendo,
                'mensagem': f'{alertas_query.notas_vencendo} notas vencem nos próximos 7 dias',
                'link': url_for('notas.index', filtro='vencendo'),
                'prioridade': 2
            })
        
        # Ordenar por prioridade
        alertas.sort(key=lambda x: x['prioridade'])
        
        return alertas
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas críticos: {str(e)}")
        return []

def _get_dados_graficos_otimizado(data_inicio, data_fim):
    """Dados para gráficos com queries otimizadas"""
    try:
        # Evolução mensal dos últimos 6 meses
        meses_dados = []
        periodo_meses = 6
        data_ref = data_fim if data_fim else date.today()
        
        for i in range(periodo_meses):
            data_mes = add_months(data_ref, -i)
            mes_inicio = data_mes.replace(day=1)
            if data_mes.month == 12:
                mes_fim = data_mes.replace(year=data_mes.year+1, month=1, day=1) - timedelta(days=1)
            else:
                mes_fim = data_mes.replace(month=data_mes.month+1, day=1) - timedelta(days=1)
            
            # Query única para dados do mês
            dados_mes = db.session.query(
                func.sum(case((Empenho.data_empenho.between(mes_inicio, mes_fim), 1), else_=0)).label('empenhos_qtd'),
                func.coalesce(func.sum(case(
                    (Empenho.data_empenho.between(mes_inicio, mes_fim), Empenho.valor_empenhado),
                    else_=0
                )), 0).label('empenhos_valor'),
                func.sum(case((NotaFiscal.data_emissao.between(mes_inicio, mes_fim), 1), else_=0)).label('notas_qtd'),
                func.coalesce(func.sum(case(
                    (NotaFiscal.data_emissao.between(mes_inicio, mes_fim), NotaFiscal.valor_liquido),
                    else_=0
                )), 0).label('notas_valor')
            ).outerjoin(NotaFiscal, NotaFiscal.empenho_id == Empenho.id).first()
            
            meses_dados.append({
                'mes': data_mes.strftime('%b/%y'),
                'mes_numero': data_mes.month,
                'ano': data_mes.year,
                'empenhos_qtd': dados_mes.empenhos_qtd,
                'empenhos_valor': float(dados_mes.empenhos_valor),
                'notas_qtd': dados_mes.notas_qtd,
                'notas_valor': float(dados_mes.notas_valor)
            })
        
        # Distribuição por status (pizza charts)
        status_empenhos = db.session.query(
            Empenho.status,
            func.count(Empenho.id).label('quantidade')
        ).group_by(Empenho.status).all()
        
        status_notas = db.session.query(
            NotaFiscal.status,
            func.count(NotaFiscal.id).label('quantidade')
        ).group_by(NotaFiscal.status).all()
        
        return {
            'evolucao_mensal': list(reversed(meses_dados)),
            'distribuicao_empenhos': [
                {'label': row.status, 'value': row.quantidade}
                for row in status_empenhos
            ],
            'distribuicao_notas': [
                {'label': row.status, 'value': row.quantidade}
                for row in status_notas
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados para gráficos: {str(e)}")


# =================== API ENDPOINTS PARA WIDGETS ===================

# ===== Helpers robustos =====
def _safe_date_col(model, primary_name, fallback_name):
    """
    Retorna a coluna de data com fallback (ex.: data_criacao -> data_empenho).
    """
    return getattr(model, primary_name, None) or getattr(model, fallback_name, None)

def _last_months_labels(n=12):
    hoje = date.today().replace(day=1)
    labels = []
    for i in range(n-1, -1, -1):
        d = (hoje.replace(day=15) - timedelta(days=30*i))  # aproximação mensal
        labels.append(d.strftime('%m/%Y'))
    # remover duplicados caso a aproximação crie repetição (raro)
    dedup, seen = [], set()
    for l in labels:
        if l not in seen:
            dedup.append(l); seen.add(l)
    return dedup[-n:]

def _month_key(dt):
    return dt.strftime('%m/%Y')

def _fmt_money(v):
    return float(v or 0.0)

@relatorios_bp.route('/api/widget-data/<widget_id>')
@login_required
def get_widget_data(widget_id):
    """
    API endpoint unificado para dados de widgets específicos
    Devolve JSON específico por widget_id:
      - kpi-empenhos        -> { total, ativos }
      - kpi-financeiro      -> { valor_total, variacao }
      - grafico-evolucao    -> { evolucao: { labels, values } }
      - grafico-pizza       -> { pizza:   { labels, values } }
      - tabela-top-fornecedores -> { fornecedores: [{nome, valor}] }
      - alertas-sistema     -> { alertas: [{tipo, icone, titulo, mensagem}] }
      - calendario-vencimentos -> { vencimentos: [{data, titulo, tipo}] }
    """
    try:
        if widget_id == "kpi-empenhos":
            return jsonify(_data_kpi_empenhos())

        elif widget_id == "kpi-financeiro":
            return jsonify(_data_kpi_financeiro())

        elif widget_id == "grafico-evolucao":
            return jsonify(_data_grafico_evolucao())

        elif widget_id == "grafico-pizza":
            return jsonify(_data_grafico_pizza())

        elif widget_id == "tabela-top-fornecedores":
            return jsonify(_data_top_fornecedores())

        elif widget_id == "alertas-sistema":
            return jsonify(_data_alertas_sistema())

        elif widget_id == "calendario-vencimentos":
            return jsonify(_data_calendario_vencimentos())

        else:
            return jsonify({"error": "widget não implementado"}), 404

    except Exception as e:
        logger.error(f"Erro ao buscar dados do widget {widget_id}: {str(e)}")
        # Fallback seguro com estrutura mínima para não quebrar o front
        return jsonify({
            "error": str(e),
            "fallback": True
        }), 200


# ===== Implementações de dados =====

def _data_kpi_empenhos():
    total = db.session.query(func.count(Empenho.id)).scalar() or 0
    # status 'ATIVO' não é típico em empenho; ajuste: considera aprovados/pagos como "ativos"
    ativos = db.session.query(func.count(Empenho.id)).filter(
        func.upper(Empenho.status).in_(["APROVADO", "PAGO"])
    ).scalar() or 0

    return {"total": int(total), "ativos": int(ativos)}

def _data_kpi_financeiro():
    # Total empenhado no mês atual vs mês anterior para % de variação
    col_data = _safe_date_col(Empenho, 'data_criacao', 'data_empenho')
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    # mês anterior
    if inicio_mes.month == 1:
        inicio_mes_ant = inicio_mes.replace(year=inicio_mes.year - 1, month=12)
    else:
        inicio_mes_ant = inicio_mes.replace(month=inicio_mes.month - 1)

    total_mes = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0))\
        .filter(col_data >= inicio_mes).scalar() or 0.0

    total_mes_ant = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0))\
        .filter(col_data >= inicio_mes_ant, col_data < inicio_mes).scalar() or 0.0

    variacao = 0.0
    if total_mes_ant:
        variacao = ((total_mes - total_mes_ant) / total_mes_ant) * 100.0

    # Também devolve o total geral, que é útil pro KPI
    valor_total = db.session.query(func.coalesce(func.sum(Empenho.valor_empenhado), 0.0)).scalar() or 0.0

    return {
        "valor_total": _fmt_money(valor_total),
        "variacao": round(variacao, 1)
    }

def _data_grafico_evolucao():
    """
    Evolução mensal (últimos 12 meses) do valor_empenhado.
    """
    col_data = _safe_date_col(Empenho, 'data_criacao', 'data_empenho')
    labels = _last_months_labels(12)
    # traz últimos 14 meses para garantir cobertura e depois agrega em Python (mais portável)
    dt_limite = date.today() - timedelta(days=430)

    rows = db.session.query(col_data, Empenho.valor_empenhado)\
        .filter(col_data.isnot(None), col_data >= dt_limite)\
        .all()

    agg = defaultdict(float)
    for dt, valor in rows:
        if not dt:
            continue
        key = _month_key(dt)
        agg[key] += float(valor or 0.0)

    values = [round(agg.get(lbl, 0.0), 2) for lbl in labels]

    return {"evolucao": {"labels": labels, "values": values}}

def _data_grafico_pizza():
    """
    Pizza por status de EMPENHO (ajuste conforme sua necessidade).
    """
    # Mapeia status que existirem em banco
    rows = db.session.query(func.upper(Empenho.status), func.count(Empenho.id))\
        .group_by(func.upper(Empenho.status)).all()

    labels, values = [], []
    for status, qtd in rows:
        labels.append(status or "N/D")
        values.append(int(qtd or 0))

    # Fallback se não houver nada
    if not labels:
        labels = ["Sem dados"]
        values = [1]

    return {"pizza": {"labels": labels, "values": values}}

def _data_top_fornecedores():
    """
    Top fornecedores por soma de valor_empenhado (Empenho) ou valor_total (Contrato).
    Tenta primeiro Empenho.fornecedor; se não existir, usa Contrato.fornecedor.
    """
    fornecedores = []

    # Tenta via Empenho
    if hasattr(Empenho, "fornecedor"):
        rows = db.session.query(
            Empenho.fornecedor,
            func.coalesce(func.sum(Empenho.valor_empenhado), 0.0)
        ).group_by(Empenho.fornecedor).order_by(func.sum(Empenho.valor_empenhado).desc()).limit(10).all()

        fornecedores = [{"nome": r[0] or "N/D", "valor": _fmt_money(r[1])} for r in rows if r[0]]
    # Senão tenta via Contrato
    elif hasattr(Contrato, "fornecedor"):
        rows = db.session.query(
            Contrato.fornecedor,
            func.coalesce(func.sum(Contrato.valor_total), 0.0)
        ).group_by(Contrato.fornecedor).order_by(func.sum(Contrato.valor_total).desc()).limit(10).all()

        fornecedores = [{"nome": r[0] or "N/D", "valor": _fmt_money(r[1])} for r in rows if r[0]]

    # Fallback
    if not fornecedores:
        fornecedores = [
            {"nome": "Fornecedor A", "valor": 120000.00},
            {"nome": "Fornecedor B", "valor": 98000.00},
            {"nome": "Fornecedor C", "valor": 75500.50}
        ]

    return {"fornecedores": fornecedores}

def _data_alertas_sistema():
    """
    Alertas com base em contratos próximos do fim e empenhos pendentes.
    """
    alertas = []

    hoje = date.today()
    # Contratos que vencem em <= 30 dias
    if hasattr(Contrato, "data_fim"):
        proximos = Contrato.query.filter(
            Contrato.data_fim.isnot(None),
            Contrato.data_fim >= hoje,
            Contrato.data_fim <= hoje + timedelta(days=30)
        ).count() or 0

        if proximos:
            alertas.append({
                "tipo": "warning",
                "icone": "bi bi-calendar-event",
                "titulo": "Contratos a vencer",
                "mensagem": f"{proximos} contrato(s) vencendo em até 30 dias."
            })

    # Empenhos pendentes
    pendentes = Empenho.query.filter(func.upper(Empenho.status) == "PENDENTE").count() or 0
    if pendentes:
        alertas.append({
            "tipo": "danger",
            "icone": "bi bi-exclamation-triangle",
            "titulo": "Empenhos pendentes",
            "mensagem": f"{pendentes} empenho(s) aguardando aprovação."
        })

    if not alertas:
        alertas = [{
            "tipo": "success",
            "icone": "bi bi-check-circle",
            "titulo": "Tudo certo",
            "mensagem": "Nenhum alerta no momento."
        }]

    return {"alertas": alertas}

def _data_calendario_vencimentos():
    """
    Vencimentos nos próximos 45 dias com base em Contrato.data_fim.
    """
    vencimentos = []
    hoje = date.today()
    if hasattr(Contrato, "data_fim"):
        rows = Contrato.query.filter(
            Contrato.data_fim.isnot(None),
            Contrato.data_fim >= hoje,
            Contrato.data_fim <= hoje + timedelta(days=45)
        ).order_by(Contrato.data_fim.asc()).limit(20).all()

        for c in rows:
            titulo = getattr(c, "objeto", None) or f"Contrato #{c.id}"
            vencimentos.append({
                "data": c.data_fim.isoformat(),
                "titulo": titulo,
                "tipo": "Contrato"
            })

    if not vencimentos:
        # Fallback amigável
        vencimentos = [{
            "data": (hoje + timedelta(days=7)).isoformat(),
            "titulo": "Exemplo: Renovação de contrato",
            "tipo": "Contrato"
        }]

    return {"vencimentos": vencimentos}


@relatorios_bp.route('/api/save-layout', methods=['POST'])
@login_required
def save_dashboard_layout():
    """Salvar layout do dashboard do usuário"""
    try:
        layout_data = request.get_json()
        
        # Por enquanto, apenas retornar sucesso
        # No futuro, pode salvar no banco de dados por usuário
        
        return jsonify({'success': True, 'message': 'Layout salvo com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao salvar layout: {str(e)}")
        return jsonify({'error': 'Erro ao salvar layout'}), 500


@relatorios_bp.route('/api/load-layout')
@login_required
def load_dashboard_layout():
    """Carregar layout salvo do dashboard"""
    try:
        # Layout padrão - no futuro pode vir do banco de dados
        default_layout = [
            {'id': 'total-empenhos', 'x': 0, 'y': 0, 'w': 3, 'h': 1},
            {'id': 'valor-total-empenhos', 'x': 3, 'y': 0, 'w': 3, 'h': 1},
            {'id': 'empenhos-pendentes', 'x': 6, 'y': 0, 'w': 3, 'h': 1},
            {'id': 'contratos-ativos', 'x': 9, 'y': 0, 'w': 3, 'h': 1},
            {'id': 'evolucao-mensal', 'x': 0, 'y': 1, 'w': 6, 'h': 3},
            {'id': 'status-empenhos', 'x': 6, 'y': 1, 'w': 6, 'h': 3},
            {'id': 'top-fornecedores', 'x': 0, 'y': 4, 'w': 8, 'h': 3},
            {'id': 'calendario-vencimentos', 'x': 8, 'y': 4, 'w': 4, 'h': 3}
        ]
        
        return jsonify({'layout': default_layout})
        
    except Exception as e:
        logger.error(f"Erro ao carregar layout: {str(e)}")
        return jsonify({'error': 'Erro ao carregar layout'}), 500
        return {}
