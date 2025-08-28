"""
API endpoints para acessar dados integrados entre contratos, empenhos e notas fiscais
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import text
from extensions import db

api_integracoes = Blueprint('api_integracoes', __name__, url_prefix='/api/integracoes')

@api_integracoes.route('/contratos-integrados')
def contratos_integrados():
    """Retorna contratos com dados integrados de empenhos"""
    try:
        sql = text("""
            SELECT * FROM view_contratos_integrados 
            ORDER BY data_inicio DESC
        """)
        result = db.session.execute(sql)
        contratos = []
        
        for row in result:
            contratos.append({
                'id': row.id,
                'numero_contrato': row.numero_contrato,
                'fornecedor': row.fornecedor,
                'objeto': row.objeto,
                'valor_total': float(row.valor_total or 0),
                'valor_empenhado_total': float(row.valor_empenhado_total or 0),
                'qtd_empenhos': row.qtd_empenhos or 0,
                'percentual_execucao': float(row.percentual_execucao or 0),
                'data_inicio': row.data_inicio.isoformat() if row.data_inicio else None,
                'data_fim': row.data_fim.isoformat() if row.data_fim else None,
                'status': row.status
            })
        
        return jsonify({
            'success': True,
            'data': contratos,
            'total': len(contratos)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_integracoes.route('/empenhos-integrados')
def empenhos_integrados():
    """Retorna empenhos com dados integrados de contratos"""
    try:
        sql = text("""
            SELECT * FROM view_empenhos_integrados 
            ORDER BY data_empenho DESC
        """)
        result = db.session.execute(sql)
        empenhos = []
        
        for row in result:
            empenhos.append({
                'id': row.id,
                'numero_empenho': row.numero_empenho,
                'numero_pregao': row.numero_pregao,
                'valor_empenhado': float(row.valor_empenhado or 0),
                'data_empenho': row.data_empenho.isoformat() if row.data_empenho else None,
                'status': row.status,
                'contrato_id': row.contrato_id,
                'contrato_numero': row.contrato_numero,
                'contrato_valor_total': float(row.contrato_valor_total or 0),
                'contrato_fornecedor': row.contrato_fornecedor,
                'percentual_contrato': float(row.percentual_contrato or 0)
            })
        
        return jsonify({
            'success': True,
            'data': empenhos,
            'total': len(empenhos)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_integracoes.route('/notas-integradas')
def notas_integradas():
    """Retorna notas fiscais com dados integrados de empenhos e contratos"""
    try:
        sql = text("""
            SELECT * FROM view_notas_integradas 
            ORDER BY data_emissao DESC
        """)
        result = db.session.execute(sql)
        notas = []
        
        for row in result:
            notas.append({
                'id': row.id,
                'numero_nota': row.numero_nota,
                'valor_total': float(row.valor_total or 0),
                'data_emissao': row.data_emissao.isoformat() if row.data_emissao else None,
                'data_vencimento': row.data_vencimento.isoformat() if row.data_vencimento else None,
                'status': row.status,
                'empenho_id': row.empenho_id,
                'empenho_numero': row.empenho_numero,
                'empenho_valor': float(row.empenho_valor or 0),
                'contrato_id': row.contrato_id,
                'contrato_numero': row.contrato_numero,
                'contrato_fornecedor': row.contrato_fornecedor,
                'percentual_empenho': float(row.percentual_empenho or 0)
            })
        
        return jsonify({
            'success': True,
            'data': notas,
            'total': len(notas)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_integracoes.route('/dashboard-summary')
def dashboard_summary():
    """Retorna resumo para dashboard com dados integrados"""
    try:
        # Resumo de contratos
        sql_contratos = text("""
            SELECT 
                COUNT(*) as total_contratos,
                SUM(valor_total) as valor_total_contratos,
                SUM(valor_empenhado_total) as valor_total_empenhado,
                AVG(percentual_execucao) as media_execucao
            FROM view_contratos_integrados
        """)
        
        # Resumo de empenhos
        sql_empenhos = text("""
            SELECT 
                COUNT(*) as total_empenhos,
                SUM(valor_empenhado) as valor_total_empenhos
            FROM view_empenhos_integrados
        """)
        
        # Resumo de notas
        sql_notas = text("""
            SELECT 
                COUNT(*) as total_notas,
                SUM(valor_total) as valor_total_notas
            FROM view_notas_integradas
        """)
        
        contratos_result = db.session.execute(sql_contratos).fetchone()
        empenhos_result = db.session.execute(sql_empenhos).fetchone()
        notas_result = db.session.execute(sql_notas).fetchone()
        
        return jsonify({
            'success': True,
            'data': {
                'contratos': {
                    'total': contratos_result.total_contratos or 0,
                    'valor_total': float(contratos_result.valor_total_contratos or 0),
                    'valor_empenhado': float(contratos_result.valor_total_empenhado or 0),
                    'media_execucao': float(contratos_result.media_execucao or 0)
                },
                'empenhos': {
                    'total': empenhos_result.total_empenhos or 0,
                    'valor_total': float(empenhos_result.valor_total_empenhos or 0)
                },
                'notas': {
                    'total': notas_result.total_notas or 0,
                    'valor_total': float(notas_result.valor_total_notas or 0)
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
