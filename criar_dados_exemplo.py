#!/usr/bin/env python3
"""
Script para criar dados de exemplo para demonstrar o dashboard moderno
"""
import sqlite3
from datetime import datetime, date, timedelta
import random

def criar_dados_exemplo():
    """Criar dados de exemplo no banco"""
    conn = sqlite3.connect('empenhos.db')
    cursor = conn.cursor()
    
    print('🔧 CRIANDO ESTRUTURAS DE EXEMPLO...')
    
    # Criar tabela de empenhos se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY,
        numero_empenho TEXT,
        valor_empenhado REAL,
        data_empenho DATE,
        status TEXT DEFAULT 'ATIVO',
        fornecedor TEXT,
        objeto TEXT
    )
    ''')
    
    # Criar tabela de contratos se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY,
        numero_contrato TEXT,
        valor_total REAL,
        data_assinatura DATE,
        status TEXT DEFAULT 'ATIVO',
        fornecedor TEXT,
        objeto TEXT
    )
    ''')
    
    # Verificar se já existem dados
    cursor.execute('SELECT COUNT(*) FROM empenhos')
    if cursor.fetchone()[0] == 0:
        print('📑 Inserindo empenhos de exemplo...')
        
        # Dados de exemplo mais realistas
        empenhos_exemplo = []
        fornecedores = [
            'CONSTRUTORA ALPHA LTDA',
            'TECH SOLUTIONS S/A',
            'VERDE LIMPO SERVIÇOS',
            'MATERIAL CENTER LTDA',
            'PAPELARIA ESCRITÓRIO',
            'AUTO POSTO COMBUSTÍVEL',
            'EMPRESA SEGURANÇA TOTAL',
            'MANUTENÇÃO & CIA',
            'UNIFORMES PROFISSIONAIS',
            'EQUIPAMENTOS MODERNOS'
        ]
        
        objetos = [
            'Material de escritório e papelaria',
            'Equipamentos de informática',
            'Serviços de limpeza e conservação',
            'Material de construção',
            'Combustível para veículos',
            'Serviços de segurança',
            'Manutenção predial',
            'Uniformes para servidores',
            'Equipamentos médicos',
            'Material de expediente'
        ]
        
        # Criar empenhos dos últimos 6 meses
        hoje = date.today()
        for i in range(50):  # 50 empenhos
            # Data aleatória nos últimos 6 meses
            dias_atras = random.randint(0, 180)
            data_empenho = hoje - timedelta(days=dias_atras)
            
            # Status aleatório com maior chance de ATIVO
            status_opcoes = ['ATIVO', 'ATIVO', 'ATIVO', 'FINALIZADO', 'CANCELADO']
            status = random.choice(status_opcoes)
            
            # Valor aleatório
            valor = round(random.uniform(1000, 100000), 2)
            
            # Fornecedor e objeto aleatórios
            fornecedor = random.choice(fornecedores)
            objeto = random.choice(objetos)
            
            empenhos_exemplo.append((
                f'2024/{i+1:03d}',
                valor,
                data_empenho.strftime('%Y-%m-%d'),
                status,
                fornecedor,
                objeto
            ))
        
        for emp in empenhos_exemplo:
            cursor.execute('''
                INSERT INTO empenhos (numero_empenho, valor_empenhado, data_empenho, status, fornecedor, objeto)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', emp)
    
    cursor.execute('SELECT COUNT(*) FROM contratos')
    if cursor.fetchone()[0] == 0:
        print('📄 Inserindo contratos de exemplo...')
        
        contratos_exemplo = [
            ('CTR-2024/001', 150000.00, '2024-01-10', 'ATIVO', 'CONSTRUTORA ALPHA LTDA', 'Reforma do prédio municipal'),
            ('CTR-2024/002', 80000.00, '2024-02-01', 'ATIVO', 'TECH SOLUTIONS S/A', 'Manutenção sistema informática'),
            ('CTR-2024/003', 45000.00, '2024-02-15', 'FINALIZADO', 'VERDE LIMPO SERVIÇOS', 'Serviços de jardinagem'),
            ('CTR-2024/004', 200000.00, '2024-03-01', 'ATIVO', 'OBRAS & CIA LTDA', 'Pavimentação de ruas'),
            ('CTR-2024/005', 120000.00, '2024-03-15', 'ATIVO', 'MATERIAL CENTER LTDA', 'Fornecimento de materiais'),
            ('CTR-2024/006', 90000.00, '2024-04-01', 'ATIVO', 'SEGURANÇA TOTAL', 'Serviços de vigilância'),
            ('CTR-2024/007', 35000.00, '2024-04-10', 'FINALIZADO', 'UNIFORMES PROFISSIONAIS', 'Uniforme para servidores'),
            ('CTR-2024/008', 180000.00, '2024-05-01', 'ATIVO', 'EQUIPAMENTOS MODERNOS', 'Equipamentos hospitalares'),
        ]
        
        for ctr in contratos_exemplo:
            cursor.execute('''
                INSERT INTO contratos (numero_contrato, valor_total, data_assinatura, status, fornecedor, objeto)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ctr)
    
    conn.commit()
    conn.close()
    
    print('✅ Dados de exemplo criados com sucesso!')
    print('🎯 Dashboard agora possui dados para exibir')
    
    # Verificar dados criados
    conn = sqlite3.connect('empenhos.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM empenhos')
    total_empenhos = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM contratos')
    total_contratos = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(valor_empenhado) FROM empenhos')
    valor_empenhado = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(valor_total) FROM contratos')
    valor_contratos = cursor.fetchone()[0] or 0
    
    print(f'\n📊 RESUMO DOS DADOS CRIADOS:')
    print(f'📑 Total de empenhos: {total_empenhos}')
    print(f'📄 Total de contratos: {total_contratos}')
    print(f'💰 Valor empenhado: R$ {valor_empenhado:,.2f}')
    print(f'💼 Valor contratado: R$ {valor_contratos:,.2f}')
    
    conn.close()

if __name__ == '__main__':
    criar_dados_exemplo()
