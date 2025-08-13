from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from models import Empenho, Contrato, db
from utils.export import ExportUtils
from utils.import_data import ImportUtils
from datetime import datetime, date
from sqlalchemy import func, extract
import os

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/')
@login_required
def index():
    """Dashboard de relatórios"""
    # Estatísticas gerais
    total_empenhos = Empenho.query.count()
    valor_total_empenhado = db.session.query(func.sum(Empenho.valor_empenhado)).scalar() or 0
    valor_total_liquido = db.session.query(func.sum(Empenho.valor_liquido)).scalar() or 0
    
    # Empenhos por status
    empenhos_por_status = db.session.query(
        Empenho.status,
        func.count(Empenho.id).label('quantidade'),
        func.sum(Empenho.valor_empenhado).label('valor_total')
    ).group_by(Empenho.status).all()
    
    # Empenhos por mês (últimos 12 meses)
    empenhos_por_mes = db.session.query(
        extract('year', Empenho.data_empenho).label('ano'),
        extract('month', Empenho.data_empenho).label('mes'),
        func.count(Empenho.id).label('quantidade'),
        func.sum(Empenho.valor_empenhado).label('valor_total')
    ).group_by('ano', 'mes').order_by('ano', 'mes').limit(12).all()
    
    # Top 10 contratos por valor
    top_contratos = db.session.query(
        Empenho.numero_contrato,
        func.sum(Empenho.valor_empenhado).label('valor_total'),
        func.count(Empenho.id).label('quantidade')
    ).group_by(Empenho.numero_contrato).order_by(func.sum(Empenho.valor_empenhado).desc()).limit(10).all()
    
    return render_template('relatorios/dashboard.html',
                         total_empenhos=total_empenhos,
                         valor_total_empenhado=valor_total_empenhado,
                         valor_total_liquido=valor_total_liquido,
                         empenhos_por_status=empenhos_por_status,
                         empenhos_por_mes=empenhos_por_mes,
                         top_contratos=top_contratos)

@relatorios_bp.route('/filtrado')
@login_required
def filtrado():
    """Relatório com filtros personalizados"""
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status = request.args.get('status')
    contrato = request.args.get('contrato')
    pregao = request.args.get('pregao')
    
    query = Empenho.query
    
    # Aplicar filtros
    if data_inicio:
        query = query.filter(Empenho.data_empenho >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    
    if data_fim:
        query = query.filter(Empenho.data_empenho <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    
    if status:
        query = query.filter(Empenho.status == status)
    
    if contrato:
        query = query.filter(Empenho.numero_contrato.contains(contrato))
    
    if pregao:
        query = query.filter(Empenho.numero_pregao.contains(pregao))
    
    empenhos = query.order_by(Empenho.data_empenho.desc()).all()
    
    # Calcular totais
    valor_total_empenhado = sum([e.valor_empenhado or 0 for e in empenhos])
    valor_total_liquido = sum([e.valor_liquido or 0 for e in empenhos])
    valor_total_retencao = sum([e.valor_retencao or 0 for e in empenhos])
    
    return render_template('relatorios/filtrado.html',
                         empenhos=empenhos,
                         valor_total_empenhado=valor_total_empenhado,
                         valor_total_liquido=valor_total_liquido,
                         valor_total_retencao=valor_total_retencao,
                         filtros={
                             'data_inicio': data_inicio,
                             'data_fim': data_fim,
                             'status': status,
                             'contrato': contrato,
                             'pregao': pregao
                         })

@relatorios_bp.route('/exportar/excel')
@login_required
def exportar_excel():
    """Exportar relatório para Excel"""
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
        
        # Gerar arquivo Excel
        filename = ExportUtils.export_to_excel(empenhos)
        
        return send_file(filename, as_attachment=True, download_name=f'relatorio_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
    except Exception as e:
        flash(f'Erro ao exportar para Excel: {str(e)}', 'error')
        return redirect(url_for('relatorios.index'))

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
        
        # Gerar arquivo PDF
        filename = ExportUtils.export_to_pdf(empenhos, filtros)
        
        return send_file(filename, as_attachment=True, download_name=f'relatorio_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
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
        
        if file and ImportUtils.allowed_file(file.filename):
            try:
                # Salvar arquivo temporariamente
                filename = ImportUtils.save_uploaded_file(file)
                
                # Importar dados
                resultado = ImportUtils.import_from_file(filename, current_user.id)
                
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
        dados = db.session.query(
            extract('year', Empenho.data_empenho).label('ano'),
            extract('month', Empenho.data_empenho).label('mes'),
            func.count(Empenho.id).label('quantidade'),
            func.sum(Empenho.valor_empenhado).label('valor_total')
        ).group_by('ano', 'mes').order_by('ano', 'mes').limit(12).all()
        
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
        filename = ExportUtils.create_backup()
        return send_file(filename, as_attachment=True, download_name=f'backup_empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    except Exception as e:
        flash(f'Erro ao gerar backup: {str(e)}', 'error')
        return redirect(url_for('relatorios.index'))
