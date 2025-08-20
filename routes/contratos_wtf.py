# routes/contratos_wtf.py
# Formulário WTForms com validação robusta e CSRF
import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db, Contrato, ItemContrato
from forms.contrato import ContratoForm

contratos_wtf_bp = Blueprint('contratos_wtf', __name__, url_prefix='/contratos-wtf')

def _upload_dir():
    d = os.path.join(current_app.instance_path, 'uploads', 'contratos')
    os.makedirs(d, exist_ok=True)
    return d

def processar_campos_extras_responsavel(form_data):
    """Processa campos extras de email e telefone do responsável"""
    emails_extras = []
    telefones_extras = []
    
    # Processar emails extras
    if 'responsavel_emails_extras[]' in form_data:
        emails_raw = form_data.getlist('responsavel_emails_extras[]')
        emails_extras = [email.strip() for email in emails_raw if email.strip()]
    
    # Processar telefones extras
    if 'responsavel_telefones_extras[]' in form_data:
        telefones_raw = form_data.getlist('responsavel_telefones_extras[]')
        telefones_extras = [tel.strip() for tel in telefones_raw if tel.strip()]
    
    return emails_extras, telefones_extras

def processar_itens_contrato(contrato, form_data):
    """Processa os itens do contrato enviados pelo formulário"""
    # Primeiro, remover itens existentes se for edição
    if contrato.id:
        ItemContrato.query.filter_by(contrato_id=contrato.id).delete()
    
    # Processar novos itens
    index = 0
    while f'itens[{index}][item]' in form_data:
        item_data = {
            'lote': form_data.get(f'itens[{index}][lote]', ''),
            'item': form_data.get(f'itens[{index}][item]'),
            'descricao': form_data.get(f'itens[{index}][descricao]'),
            'marca': form_data.get(f'itens[{index}][marca]', ''),
            'quantidade': form_data.get(f'itens[{index}][quantidade]'),
            'unidade': form_data.get(f'itens[{index}][unidade]'),
            'valor_unitario': form_data.get(f'itens[{index}][valor_unitario]'),
        }
        
        # Validar dados obrigatórios
        if not all([item_data['item'], item_data['descricao'], 
                   item_data['quantidade'], item_data['unidade'], 
                   item_data['valor_unitario']]):
            index += 1
            continue
        
        try:
            # Criar item
            item = ItemContrato(
                contrato_id=contrato.id,
                lote=item_data['lote'] or None,
                item=item_data['item'],
                descricao=item_data['descricao'],
                marca=item_data['marca'] or None,
                quantidade=float(item_data['quantidade']),
                unidade=item_data['unidade'],
                valor_unitario=float(item_data['valor_unitario'])
            )
            
            # Calcular valor total automaticamente
            item.calcular_valor_total()
            
            db.session.add(item)
            
        except (ValueError, TypeError) as e:
            # Pular item com dados inválidos
            current_app.logger.warning(f'Item inválido ignorado: {str(e)}')
            pass
        
        index += 1

@contratos_wtf_bp.get('/novo')
def novo():
    form = ContratoForm()
    return render_template('contratos/form_wtf.html', form=form, contrato=None)

@contratos_wtf_bp.post('/novo')
def criar():
    form = ContratoForm()
    if form.validate_on_submit():
        c = Contrato()
        
        # Atribuições explícitas dos campos do form para o modelo
        c.numero_pregao = form.numero_pregao.data
        c.numero_contrato = form.numero_contrato.data
        c.numero_processo = form.numero_processo.data
        c.ano_pregao = form.ano_pregao.data
        c.ano_contrato = form.ano_contrato.data
        c.ano_processo = form.ano_processo.data
        c.objeto = form.objeto.data
        c.lei_base = form.lei_base.data
        c.modalidade_licitacao = form.modalidade_licitacao.data or None
        c.orgao_contratante = form.orgao_contratante.data
        c.secretaria = form.secretaria.data
        c.fornecedor = form.fornecedor.data
        c.cnpj_fornecedor = form.cnpj_fornecedor.data
        c.responsavel_nome = form.responsavel_nome.data
        c.responsavel_cargo = form.responsavel_cargo.data
        c.responsavel_email = form.responsavel_email.data
        c.responsavel_telefone = form.responsavel_telefone.data
        
        # Processar campos extras de email e telefone
        emails_extras, telefones_extras = processar_campos_extras_responsavel(request.form)
        c.responsavel_emails_extras = json.dumps(emails_extras) if emails_extras else None
        c.responsavel_telefones_extras = json.dumps(telefones_extras) if telefones_extras else None
        c.valor_total = form.valor_total.data
        c.valor_inicial = form.valor_inicial.data
        c.data_assinatura = form.data_assinatura.data
        c.data_inicio = form.data_inicio.data
        c.data_fim = form.data_fim.data
        c.data_fim_original = None  # Campo removido, deixando nulo
        c.gestor_fiscal = form.gestor_fiscal.data
        c.gestor_superior = form.gestor_superior.data
        c.tipo_garantia = form.tipo_garantia.data or None
        c.valor_garantia = form.valor_garantia.data
        c.validade_garantia = form.validade_garantia.data
        c.observacoes = form.observacoes.data

        # Upload de arquivo
        f = form.arquivo_contrato.data
        if f and getattr(f, "filename", ""):
            filename = secure_filename(f.filename)
            upload_dir = _upload_dir()
            path = os.path.join(upload_dir, filename)
            f.save(path)
            c.arquivo_contrato = filename

        try:
            db.session.add(c)
            db.session.commit()
            
            # Processar itens do contrato após salvar o contrato
            processar_itens_contrato(c, request.form)
            db.session.commit()
            
            flash("Contrato criado com sucesso!", "success")
            return redirect(url_for('contratos.detalhes', id=c.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar contrato: {str(e)}", "error")
    else:
        # erros de validação aparecem no template
        flash("Verifique os campos destacados.", "warning")
    
    return render_template('contratos/form_wtf.html', form=form, contrato=None), 400

@contratos_wtf_bp.get('/<int:id>/editar')
def editar(id):
    c = Contrato.query.get_or_404(id)
    form = ContratoForm(obj=c)
    return render_template('contratos/form_wtf.html', form=form, contrato=c)

@contratos_wtf_bp.post('/<int:id>/editar')
def atualizar(id):
    c = Contrato.query.get_or_404(id)
    form = ContratoForm()
    
    if form.validate_on_submit():
        # Atualizar campos
        c.numero_pregao = form.numero_pregao.data
        c.numero_contrato = form.numero_contrato.data
        c.numero_processo = form.numero_processo.data
        c.ano_pregao = form.ano_pregao.data
        c.ano_contrato = form.ano_contrato.data
        c.ano_processo = form.ano_processo.data
        c.objeto = form.objeto.data
        c.lei_base = form.lei_base.data
        c.modalidade_licitacao = form.modalidade_licitacao.data or None
        c.orgao_contratante = form.orgao_contratante.data
        c.secretaria = form.secretaria.data
        c.fornecedor = form.fornecedor.data
        c.cnpj_fornecedor = form.cnpj_fornecedor.data
        c.responsavel_nome = form.responsavel_nome.data
        c.responsavel_cargo = form.responsavel_cargo.data
        c.responsavel_email = form.responsavel_email.data
        c.responsavel_telefone = form.responsavel_telefone.data
        
        # Processar campos extras de email e telefone
        emails_extras, telefones_extras = processar_campos_extras_responsavel(request.form)
        c.responsavel_emails_extras = json.dumps(emails_extras) if emails_extras else None
        c.responsavel_telefones_extras = json.dumps(telefones_extras) if telefones_extras else None
        
        c.valor_total = form.valor_total.data
        c.valor_inicial = form.valor_inicial.data
        c.data_assinatura = form.data_assinatura.data
        c.data_inicio = form.data_inicio.data
        c.data_fim = form.data_fim.data
        c.data_fim_original = None  # Campo removido, deixando nulo
        c.gestor_fiscal = form.gestor_fiscal.data
        c.gestor_superior = form.gestor_superior.data
        c.tipo_garantia = form.tipo_garantia.data or None
        c.valor_garantia = form.valor_garantia.data
        c.validade_garantia = form.validade_garantia.data
        c.observacoes = form.observacoes.data

        # Upload de arquivo (se houver)
        f = form.arquivo_contrato.data
        if f and getattr(f, "filename", ""):
            filename = secure_filename(f.filename)
            upload_dir = _upload_dir()
            path = os.path.join(upload_dir, filename)
            f.save(path)
            c.arquivo_contrato = filename

        try:
            # Processar itens do contrato antes de fazer commit
            processar_itens_contrato(c, request.form)
            db.session.commit()
            flash("Contrato atualizado com sucesso!", "success")
            return redirect(url_for('contratos.detalhes', id=c.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar contrato: {str(e)}", "error")
    else:
        flash("Verifique os campos destacados.", "warning")
    
    return render_template('contratos/form_wtf.html', form=form, contrato=c), 400

@contratos_wtf_bp.get('/<int:id>/download')
def download_arquivo(id):
    c = Contrato.query.get_or_404(id)
    if not c.arquivo_contrato:
        flash("Contrato não possui arquivo anexado.", "warning")
        return redirect(url_for('contratos.detalhes', id=c.id))
    return send_from_directory(_upload_dir(), c.arquivo_contrato, as_attachment=True)


@contratos_wtf_bp.route('/importar-excel', methods=['POST'])
@login_required
def importar_excel():
    """Importar itens de contrato a partir de arquivo Excel"""
    try:
        if 'arquivo_excel' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo foi enviado'})
        
        file = request.files['arquivo_excel']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo foi selecionado'})
        
        # Verificar extensão do arquivo
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Formato de arquivo inválido. Use apenas .xlsx ou .xls'})
        
        # Importar bibliotecas necessárias
        import pandas as pd
        from io import BytesIO
        
        # Ler o arquivo Excel
        file_content = file.read()
        file_io = BytesIO(file_content)
        
        try:
            # Tentar ler como xlsx primeiro
            df = pd.read_excel(file_io, engine='openpyxl')
        except:
            try:
                # Se falhar, tentar como xls
                file_io.seek(0)
                df = pd.read_excel(file_io, engine='xlrd')
            except Exception as e:
                return jsonify({'success': False, 'error': f'Erro ao ler arquivo Excel: {str(e)}'})
        
        # Verificar se o DataFrame não está vazio
        if df.empty:
            return jsonify({'success': False, 'error': 'O arquivo Excel está vazio'})
        
        # Mapear colunas esperadas (flexível com diferentes nomes)
        column_mapping = {
            'lote': ['lote', 'LOTE', 'Lote', 'lote_num', 'numero_lote'],
            'item': ['item', 'ITEM', 'Item', 'codigo', 'codigo_item', 'number', 'num'],
            'descricao': ['descricao', 'DESCRIÇÃO', 'Descrição', 'description', 'produto', 'servico'],
            'marca': ['marca', 'MARCA', 'Marca', 'brand', 'fabricante'],
            'unidade': ['unidade', 'UNIDADE', 'Unidade', 'un', 'UN', 'unit'],
            'quantidade': ['quantidade', 'QUANTIDADE', 'Quantidade', 'qty', 'qtd', 'qtde'],
            'valor_unitario': ['valor_unitario', 'VALOR UNITÁRIO', 'Valor Unitário', 'valor_unit', 'preco', 'price', 'unit_price']
        }
        
        # Função para encontrar coluna correspondente
        def find_column(df_columns, possible_names):
            for name in possible_names:
                if name in df_columns:
                    return name
            return None
        
        # Mapear colunas reais
        mapped_columns = {}
        for field, possible_names in column_mapping.items():
            found_column = find_column(df.columns, possible_names)
            if found_column:
                mapped_columns[field] = found_column
        
        # Verificar se encontramos pelo menos as colunas obrigatórias
        required_fields = ['item', 'descricao', 'quantidade', 'valor_unitario']
        missing_fields = [field for field in required_fields if field not in mapped_columns]
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Colunas obrigatórias não encontradas: {", ".join(missing_fields)}. '
                        f'Colunas disponíveis: {", ".join(df.columns.tolist())}'
            })
        
        # Processar dados
        itens_importados = []
        
        for index, row in df.iterrows():
            try:
                # Extrair dados da linha
                item_data = {}
                
                for field, column in mapped_columns.items():
                    value = row[column]
                    # Tratar valores NaN
                    if pd.isna(value):
                        item_data[field] = '' if field in ['lote', 'marca'] else None
                    else:
                        item_data[field] = str(value).strip()
                
                # Validar dados obrigatórios
                if not all([item_data.get('item'), item_data.get('descricao'), 
                           item_data.get('quantidade'), item_data.get('valor_unitario')]):
                    continue  # Pular linha com dados incompletos
                
                # Converter valores numéricos
                try:
                    item_data['quantidade'] = float(str(item_data['quantidade']).replace(',', '.'))
                    item_data['valor_unitario'] = float(str(item_data['valor_unitario']).replace(',', '.'))
                except (ValueError, TypeError):
                    continue  # Pular linha com valores inválidos
                
                # Normalizar unidade se não especificada
                if not item_data.get('unidade'):
                    item_data['unidade'] = 'UN'
                
                itens_importados.append(item_data)
                
            except Exception as e:
                current_app.logger.warning(f'Erro ao processar linha {index + 1}: {str(e)}')
                continue
        
        if not itens_importados:
            return jsonify({'success': False, 'error': 'Nenhum item válido foi encontrado no arquivo'})
        
        return jsonify({
            'success': True,
            'itens': itens_importados,
            'total': len(itens_importados)
        })
        
    except Exception as e:
        current_app.logger.error(f'Erro ao importar Excel: {str(e)}')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'})
