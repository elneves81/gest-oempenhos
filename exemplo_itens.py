#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar arquivo Excel de exemplo com itens de contrato
Para testar a funcionalidade de importação
"""

import pandas as pd
import os

# Dados de exemplo para a planilha
dados_exemplo = {
    'LOTE': [1, 1, 2, 2, 3],
    'ITEM': ['001', '002', '003', '004', '005'],
    'DESCRIÇÃO': [
        'Papel sulfite A4 75g/m² branco',
        'Caneta esferográfica azul',
        'Grampeador de mesa',
        'Grampos 26/6',
        'Pasta arquivo L'
    ],
    'MARCA': [
        'Report',
        'BIC',
        'Rapid',
        'Rapid',
        'Dello'
    ],
    'UNIDADE': ['PCT', 'UN', 'UN', 'CX', 'UN'],
    'QUANTIDADE': [500, 1000, 10, 50, 200],
    'VALOR UNITÁRIO': [25.50, 1.20, 45.00, 8.50, 2.75]
}

# Criar DataFrame
df = pd.DataFrame(dados_exemplo)

# Calcular valor total por item
df['VALOR TOTAL'] = df['QUANTIDADE'] * df['VALOR UNITÁRIO']

# Salvar como Excel
arquivo_saida = 'exemplo_itens_contrato.xlsx'
caminho_completo = os.path.join(os.getcwd(), arquivo_saida)

with pd.ExcelWriter(caminho_completo, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Itens', index=False)

print(f"✅ Arquivo Excel de exemplo criado: {caminho_completo}")
print(f"📊 Total de itens: {len(df)}")
print(f"💰 Valor total: R$ {df['VALOR TOTAL'].sum():.2f}")
print("\n📋 Estrutura do arquivo:")
print(df.to_string(index=False))
print(f"\n🔄 Use este arquivo para testar a importação em: http://10.0.50.79:5000/contratos-wtf/novo")
