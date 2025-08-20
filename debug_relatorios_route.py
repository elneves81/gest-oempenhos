"""Rota temporária para debug com dados mock"""

from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

debug_bp = Blueprint('debug_relatorios', __name__)

@debug_bp.route('/debug-relatorios')
@login_required
def debug_index():
    """Versão de debug com dados mock"""
    try:
        hoje = date.today()
        data_fim = hoje
        inicio_janela = (data_fim.replace(day=1) - relativedelta(months=11))

        # Dados mock para teste
        total_empenhos = 150
        valor_total_empenhado = 1500000.50
        valor_total_liquido = 1200000.30
        total_notas = 75
        valor_notas_pagas = 800000.20
        valor_notas_abertas = 400000.10

        # Mock status data
        empenhos_por_status = [
            {'status': 'ATIVO', 'quantidade': 100, 'valor_total': 1000000.0},
            {'status': 'FINALIZADO', 'quantidade': 40, 'valor_total': 400000.0},
            {'status': 'CANCELADO', 'quantidade': 10, 'valor_total': 100000.0}
        ]

        notas_por_status = [
            {'status': 'PAGO', 'quantidade': 50, 'valor_total': 800000.0},
            {'status': 'EM_ABERTO', 'quantidade': 20, 'valor_total': 400000.0},
            {'status': 'VENCIDO', 'quantidade': 5, 'valor_total': 100000.0}
        ]

        # Mock evolução mensal
        evolucao_mensal = []
        cursor = inicio_janela
        for i in range(12):
            evolucao_mensal.append({
                'mes': cursor.strftime('%b/%y'),
                'empenhos_qtd': 10 + i,
                'empenhos_valor': 100000.0 + (i * 50000),
                'notas_qtd': 5 + i,
                'notas_valor': 50000.0 + (i * 25000),
            })
            cursor += relativedelta(months=1)

        # Mock fornecedores
        top_fornecedores = [
            {'fornecedores': 'Fornecedor A Ltda', 'valor_total': 500000.0, 'quantidade': 25},
            {'fornecedores': 'Empresa B S/A', 'valor_total': 300000.0, 'quantidade': 15},
            {'fornecedores': 'Comercial C', 'valor_total': 200000.0, 'quantidade': 10}
        ]

        # Mock alertas
        alertas = [
            {'tipo': 'warning', 'titulo': 'Empenhos vencendo', 'mensagem': '5 itens nos próximos 30 dias'},
            {'tipo': 'danger', 'titulo': 'Notas vencidas', 'mensagem': '3 em atraso'}
        ]

        # Mock insights
        from routes.relatorios import _build_insights
        insights = _build_insights(evolucao_mensal, empenhos_por_status, notas_por_status)

        return render_template(
            'relatorios/dashboard_v2.html',
            total_empenhos=total_empenhos,
            valor_total_empenhado=valor_total_empenhado,
            valor_total_liquido=valor_total_liquido,
            total_notas=total_notas,
            valor_notas_pagas=valor_notas_pagas,
            valor_notas_abertas=valor_notas_abertas,
            empenhos_por_status=empenhos_por_status,
            notas_por_status=notas_por_status,
            evolucao_mensal=evolucao_mensal,
            top_fornecedores=top_fornecedores,
            alertas=alertas,
            periodo={'inicio': inicio_janela, 'fim': data_fim},
            insights=insights
        )
        
    except Exception as e:
        return f"Erro: {e}"
