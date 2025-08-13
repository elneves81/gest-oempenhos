try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from models import Empenho, db
import tempfile

class ImportUtils:
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Mapeamento de colunas (nome na planilha -> nome no modelo)
    COLUMN_MAPPING = {
        'pregao': 'numero_pregao',
        'pregão': 'numero_pregao',
        'numero_pregao': 'numero_pregao',
        'ctr': 'numero_contrato',
        'contrato': 'numero_contrato',
        'numero_contrato': 'numero_contrato',
        'aditivo': 'numero_aditivo',
        'numero_aditivo': 'numero_aditivo',
        'objeto': 'objeto',
        'objeto_microsens': 'objeto',
        'unid_mensal': 'unidade_mensal',
        'unidade_mensal': 'unidade_mensal',
        'v_unit': 'valor_unitario',
        'valor_unitario': 'valor_unitario',
        'valor_unit': 'valor_unitario',
        'empenho': 'numero_empenho',
        'numero_empenho': 'numero_empenho',
        'num_empenho': 'numero_empenho',
        'data_empenho': 'data_empenho',
        'dt_empenho': 'data_empenho',
        'valor_empenhado': 'valor_empenhado',
        'vlr_empenhado': 'valor_empenhado',
        'qtd': 'quantidade',
        'quantidade': 'quantidade',
        'valor_periodo': 'valor_periodo',
        'vlr_periodo': 'valor_periodo',
        'retencao': 'percentual_retencao',
        'percentual_retencao': 'percentual_retencao',
        'perc_retencao': 'percentual_retencao',
        'valor_retencao': 'valor_retencao',
        'vlr_retencao': 'valor_retencao',
        'valor_liquido': 'valor_liquido',
        'vlr_liquido': 'valor_liquido',
        'v_liquido': 'valor_liquido',
        'data_envio': 'data_envio',
        'dt_envio': 'data_envio',
        'data_vencimento': 'data_vencimento',
        'dt_vencimento': 'data_vencimento',
        'periodo': 'periodo_referencia',
        'periodo_referencia': 'periodo_referencia',
        'status': 'status',
        'situacao': 'status',
        'nota': 'nota_fiscal',
        'nota_fiscal': 'nota_fiscal',
        'nf': 'nota_fiscal',
        'observacoes': 'observacoes',
        'obs': 'observacoes',
        'saldo_remanescente': 'saldo_remanescente',
        'saldo': 'saldo_remanescente'
    }
    
    @staticmethod
    def allowed_file(filename):
        """Verifica se o arquivo tem extensão permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ImportUtils.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_uploaded_file(file):
        """Salva arquivo enviado temporariamente"""
        filename = secure_filename(file.filename)
        filepath = os.path.join(tempfile.gettempdir(), filename)
        file.save(filepath)
        return filepath
    
    @staticmethod
    def normalize_column_name(col_name):
        """Normaliza nome da coluna para mapeamento"""
        if col_name is None:
            return None
        
        # Converter para minúsculas e remover espaços/caracteres especiais
        normalized = str(col_name).lower().strip()
        normalized = normalized.replace(' ', '_').replace('-', '_')
        normalized = normalized.replace('(', '').replace(')', '')
        normalized = normalized.replace('ã', 'a').replace('ç', 'c')
        normalized = normalized.replace('é', 'e').replace('ê', 'e')
        normalized = normalized.replace('í', 'i').replace('ó', 'o')
        normalized = normalized.replace('ú', 'u').replace('ü', 'u')
        
        return normalized
    
    @staticmethod
    def map_columns(df):
        """Mapeia colunas da planilha para campos do modelo"""
        column_map = {}
        
        for col in df.columns:
            normalized_col = ImportUtils.normalize_column_name(col)
            if normalized_col in ImportUtils.COLUMN_MAPPING:
                column_map[col] = ImportUtils.COLUMN_MAPPING[normalized_col]
        
        return column_map
    
    @staticmethod
    def parse_date(date_value):
        """Converte valor para data"""
        if pd.isna(date_value) or date_value == '':
            return None
        
        # Se já é datetime
        if isinstance(date_value, datetime):
            return date_value.date()
        
        # Tentar diferentes formatos de data
        date_formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d/%m/%y',
            '%d-%m-%y'
        ]
        
        date_str = str(date_value).strip()
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def parse_number(value):
        """Converte valor para número"""
        if pd.isna(value) or value == '':
            return None
        
        try:
            # Remover formatação brasileira
            if isinstance(value, str):
                value = value.replace('R$', '').replace(' ', '')
                value = value.replace('.', '').replace(',', '.')
            
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def import_from_file(filepath, user_id):
        """Importa dados de arquivo Excel ou CSV"""
        resultado = {
            'sucesso': False,
            'importados': 0,
            'erros': 0,
            'mensagens_erro': [],
            'erro': None
        }
        
        try:
            # Ler arquivo
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, encoding='utf-8')
            else:
                df = pd.read_excel(filepath)
            
            if df.empty:
                resultado['erro'] = 'Arquivo vazio ou sem dados válidos'
                return resultado
            
            # Mapear colunas
            column_map = ImportUtils.map_columns(df)
            
            if not column_map:
                resultado['erro'] = 'Nenhuma coluna reconhecida encontrada no arquivo'
                return resultado
            
            # Renomear colunas
            df_mapped = df.rename(columns=column_map)
            
            # Processar cada linha
            for index, row in df_mapped.iterrows():
                try:
                    # Verificar campos obrigatórios
                    if 'numero_empenho' not in row or pd.isna(row.get('numero_empenho')):
                        resultado['erros'] += 1
                        resultado['mensagens_erro'].append(f'Linha {index + 2}: Número do empenho é obrigatório')
                        continue
                    
                    if 'valor_empenhado' not in row or pd.isna(row.get('valor_empenhado')):
                        resultado['erros'] += 1
                        resultado['mensagens_erro'].append(f'Linha {index + 2}: Valor empenhado é obrigatório')
                        continue
                    
                    # Verificar se empenho já existe
                    numero_empenho = str(row['numero_empenho']).strip()
                    if Empenho.query.filter_by(numero_empenho=numero_empenho).first():
                        resultado['erros'] += 1
                        resultado['mensagens_erro'].append(f'Linha {index + 2}: Empenho {numero_empenho} já existe')
                        continue
                    
                    # Criar objeto Empenho
                    empenho_data = {
                        'numero_empenho': numero_empenho,
                        'numero_pregao': str(row.get('numero_pregao', '')).strip(),
                        'numero_contrato': str(row.get('numero_contrato', '')).strip(),
                        'numero_aditivo': str(row.get('numero_aditivo', '')).strip() if not pd.isna(row.get('numero_aditivo')) else None,
                        'objeto': str(row.get('objeto', '')).strip(),
                        'unidade_mensal': str(row.get('unidade_mensal', '')).strip() if not pd.isna(row.get('unidade_mensal')) else None,
                        'valor_unitario': ImportUtils.parse_number(row.get('valor_unitario')),
                        'data_empenho': ImportUtils.parse_date(row.get('data_empenho')),
                        'valor_empenhado': ImportUtils.parse_number(row.get('valor_empenhado')),
                        'quantidade': ImportUtils.parse_number(row.get('quantidade')),
                        'valor_periodo': ImportUtils.parse_number(row.get('valor_periodo')),
                        'percentual_retencao': ImportUtils.parse_number(row.get('percentual_retencao')) or 0,
                        'data_envio': ImportUtils.parse_date(row.get('data_envio')),
                        'data_vencimento': ImportUtils.parse_date(row.get('data_vencimento')),
                        'periodo_referencia': str(row.get('periodo_referencia', '')).strip() if not pd.isna(row.get('periodo_referencia')) else None,
                        'status': str(row.get('status', 'PENDENTE')).strip().upper(),
                        'nota_fiscal': str(row.get('nota_fiscal', '')).strip() if not pd.isna(row.get('nota_fiscal')) else None,
                        'observacoes': str(row.get('observacoes', '')).strip() if not pd.isna(row.get('observacoes')) else None,
                        'saldo_remanescente': ImportUtils.parse_number(row.get('saldo_remanescente')) or 0
                    }
                    
                    # Criar empenho usando o método from_dict
                    empenho = Empenho.from_dict(empenho_data, user_id)
                    
                    db.session.add(empenho)
                    resultado['importados'] += 1
                    
                except Exception as e:
                    resultado['erros'] += 1
                    resultado['mensagens_erro'].append(f'Linha {index + 2}: {str(e)}')
                    continue
            
            # Salvar no banco
            db.session.commit()
            resultado['sucesso'] = True
            
        except Exception as e:
            db.session.rollback()
            resultado['erro'] = str(e)
        
        return resultado
    
    @staticmethod
    def get_template_excel():
        """Gera arquivo template para importação"""
        template_data = {
            'PREGAO': ['2024001'],
            'CTR': ['001/2024'],
            'ADITIVO': [''],
            'OBJETO': ['Exemplo de objeto do contrato'],
            'UNID_MENSAL': ['UN'],
            'V_UNIT': [100.00],
            'EMPENHO': ['2024NE000001'],
            'DATA_EMPENHO': ['01/01/2024'],
            'VALOR_EMPENHADO': [1000.00],
            'QTD': [10],
            'VALOR_PERIODO': [1000.00],
            'RETENCAO': [0],
            'VALOR_RETENCAO': [0],
            'V_LIQUIDO': [1000.00],
            'DATA_ENVIO': ['01/01/2024'],
            'DATA_VENCIMENTO': ['31/01/2024'],
            'PERIODO': ['01/2024'],
            'STATUS': ['PENDENTE'],
            'NOTA': [''],
            'OBSERVACOES': ['']
        }
        
        filename = os.path.join(tempfile.gettempdir(), f'template_importacao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
        df = pd.DataFrame(template_data)
        df.to_excel(filename, index=False)
        
        return filename
