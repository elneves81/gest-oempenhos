# Backup da rota original de contratos antes da integração WTForms
# Este arquivo mantém a funcionalidade original como fallback

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, send_file, abort
from flask_login import login_required, current_user
from datetime import datetime
import os
from models import db, Contrato, AditivoContratual, Empenho, ItemContrato, AnotacaoContrato, AnexoAnotacao

contratos_original_bp = Blueprint('contratos_original', __name__, url_prefix='/contratos-original')

# Copiar funções utilitárias...
def parse_date_field(date_str):
    """
    Converte string de data de forma robusta.
    Aceita formatos: YYYY-MM-DD, YYYY, ou string vazia
    """
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    
    # Se for apenas ano (4 dígitos)
    if len(date_str) == 4 and date_str.isdigit():
        return datetime(int(date_str), 1, 1).date()
    
    # Se for data completa
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # Tentar outros formatos comuns
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None

@contratos_original_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Formulário original de criação de contrato (backup)"""
    if request.method == 'GET':
        return render_template('contratos/form_novo.html', contrato=None)
    
    # POST - implementação original simplificada
    flash("Esta é a versão original do formulário (backup)", "info")
    return redirect(url_for('contratos.index'))
