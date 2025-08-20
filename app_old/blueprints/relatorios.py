from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, date

# Importar modelos - ajuste conforme sua estrutura
try:
    from models import Contrato, Empenho, db
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from models import Contrato, Empenho, db

bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")

@bp.route("/", methods=["GET"], endpoint="index")
@login_required
def lista():
    """Página principal de relatórios"""
    try:
        # Estatísticas básicas para o dashboard de relatórios
        total_contratos = Contrato.query.count()
        total_empenhos = Empenho.query.count()
        
        # Contratos por status
        contratos_ativos = Contrato.query.filter_by(status='ATIVO').count()
        contratos_finalizados = Contrato.query.filter_by(status='FINALIZADO').count()
        
        # Dados para gráficos (exemplo)
        dados_grafico = {
            'contratos_por_status': {
                'labels': ['Ativos', 'Finalizados', 'Outros'],
                'values': [
                    contratos_ativos, 
                    contratos_finalizados, 
                    total_contratos - contratos_ativos - contratos_finalizados
                ]
            }
        }
        
        return render_template(
            "relatorios/index.html",
            total_contratos=total_contratos,
            total_empenhos=total_empenhos,
            contratos_ativos=contratos_ativos,
            contratos_finalizados=contratos_finalizados,
            dados_grafico=dados_grafico
        )
    except Exception as e:
        # Se houver erro, renderizar template vazio
        return render_template(
            "relatorios/index.html",
            total_contratos=0,
            total_empenhos=0,
            contratos_ativos=0,
            contratos_finalizados=0,
            dados_grafico={},
            erro=str(e)
        )

@bp.route("/contratos", methods=["GET"])
@login_required
def relatorio_contratos():
    """Relatório específico de contratos"""
    try:
        # Filtros
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        
        query = Contrato.query
        
        # Aplicar filtros
        if data_inicio:
            query = query.filter(Contrato.data_inicio >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Contrato.data_fim <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        if status:
            query = query.filter(Contrato.status == status)
        
        contratos = query.all()
        
        return render_template(
            "relatorios/contratos.html",
            contratos=contratos,
            filtros={
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'status': status
            }
        )
    except Exception as e:
        return render_template(
            "relatorios/contratos.html",
            contratos=[],
            erro=str(e)
        )

@bp.route("/empenhos", methods=["GET"])
@login_required
def relatorio_empenhos():
    """Relatório específico de empenhos"""
    try:
        # Similar ao relatório de contratos
        empenhos = Empenho.query.all()
        
        return render_template(
            "relatorios/empenhos.html",
            empenhos=empenhos
        )
    except Exception as e:
        return render_template(
            "relatorios/empenhos.html",
            empenhos=[],
            erro=str(e)
        )
