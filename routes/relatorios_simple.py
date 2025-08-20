# relatorios.py - VERSÃO SIMPLIFICADA PARA DEBUG
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Empenho, Contrato, NotaFiscal, db
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, case, desc, asc, text
import logging

relatorios_bp = Blueprint('relatorios', __name__)
logger = logging.getLogger(__name__)

@relatorios_bp.route('/')
@login_required
def index():
    """Dashboard de relatórios - VERSÃO SIMPLIFICADA"""
    try:
        # Estatísticas BÁSICAS apenas
        total_empenhos = Empenho.query.count()
        total_contratos = Contrato.query.count()
        total_notas = NotaFiscal.query.count()
        
        # Contexto mínimo
        context = {
            'total_empenhos': total_empenhos,
            'total_contratos': total_contratos,
            'total_notas': total_notas,
            'valor_total_empenhado': 0.0,
            'valor_total_liquido': 0.0,
            'valor_notas_pagas': 0.0,
            'valor_notas_abertas': 0.0,
            'empenhos_por_status': [],
            'notas_por_status': [],
            'evolucao_mensal': [],
            'top_fornecedores': [],
            'alertas': [],
            'insights': [],
            'periodo': {'inicio': date.today(), 'fim': date.today()}
        }
        
        return render_template('relatorios/dashboard_v2.html', **context)
        
    except Exception as e:
        logger.error(f"Erro no dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return f'''
        <h1>Dashboard de Relatórios</h1>
        <div style="color: red;">
            <h2>Erro: {e}</h2>
            <pre>{traceback.format_exc()}</pre>
        </div>
        <p>Total de empenhos: {Empenho.query.count()}</p>
        <p>Total de contratos: {Contrato.query.count()}</p>
        <p>Total de notas: {NotaFiscal.query.count()}</p>
        '''
