# init_contratos.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o app flask diretamente
def get_flask_app():
    """Função para obter a instância do Flask app"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "app.py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    return app_module.app

# Tentar importar de diferentes formas
try:
    from app import app
except:
    try:
        import app as app_module
        app = app_module.app if hasattr(app_module, 'app') else get_flask_app()
    except:
        app = get_flask_app()

from models import db, ContratoOtimizado

with app.app_context():
    print('📋 Criando tabelas de contratos...')
    db.create_all()
    
    # Verificar se a coluna contrato_id existe na tabela empenhos
    try:
        from sqlalchemy import text
        result = db.session.execute(text('PRAGMA table_info(empenhos)')).fetchall()
        colunas = [col[1] for col in result]
        if 'contrato_id' not in colunas:
            print('➕ Adicionando coluna contrato_id na tabela empenhos...')
            db.session.execute(text('ALTER TABLE empenhos ADD COLUMN contrato_id INTEGER'))
            db.session.commit()
            print('✅ Coluna contrato_id adicionada')
        else:
            print('✅ Coluna contrato_id já existe')
    except Exception as e:
        print(f'⚠️ Erro ao verificar/adicionar coluna: {e}')
    
    # Criar alguns contratos de exemplo
    try:
        if ContratoOtimizado.query.count() == 0:
            print('📝 Criando contratos de exemplo...')
            from datetime import date, timedelta
            
            contratos_exemplo = [
                {
                    'numero': '2025/001-CT',
                    'fornecedor': 'EMPRESA DE CONSTRUÇÃO LTDA',
                    'objeto': 'Construção de ponte sobre o rio municipal',
                    'valor_inicial': 150000.00,
                    'aditivos_total': 25000.00,
                    'valor_atualizado': 175000.00,
                    'data_inicio': date.today(),
                    'data_fim': date.today() + timedelta(days=365),
                    'status': 'VIGENTE'
                },
                {
                    'numero': '2025/002-CT',
                    'fornecedor': 'FORNECEDORA DE MATERIAIS S/A',
                    'objeto': 'Fornecimento de material de limpeza',
                    'valor_inicial': 48000.00,
                    'aditivos_total': 0.00,
                    'valor_atualizado': 48000.00,
                    'data_inicio': date.today(),
                    'data_fim': date.today() + timedelta(days=180),
                    'status': 'VIGENTE'
                },
                {
                    'numero': '2024/015-CT',
                    'fornecedor': 'TRANSPORTADORA MUNICIPAL LTDA',
                    'objeto': 'Transporte escolar zona rural',
                    'valor_inicial': 95000.00,
                    'aditivos_total': 15000.00,
                    'valor_atualizado': 110000.00,
                    'empenhado_contrato': 85000.00,
                    'data_inicio': date(2024, 1, 15),
                    'data_fim': date(2024, 12, 31),
                    'status': 'ENCERRADO'
                }
            ]
            
            for dados in contratos_exemplo:
                contrato = ContratoOtimizado(**dados)
                db.session.add(contrato)
            
            db.session.commit()
            print(f'✅ {len(contratos_exemplo)} contratos de exemplo criados')
        else:
            print('✅ Contratos já existem no banco')
    except Exception as e:
        print(f'⚠️ Erro ao criar contratos de exemplo: {e}')
    
    print('🎉 Sistema de contratos inicializado com sucesso!')
