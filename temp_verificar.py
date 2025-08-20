import sqlite3
import os

db_path = os.path.join('instance', 'database.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = cursor.fetchall()
    
    print('Tabelas no banco:')
    for tabela in tabelas:
        print(f'  - {tabela[0]}')
    
    # Verificar se há tabela com 'contrato' no nome
    for tabela in tabelas:
        if 'contrato' in tabela[0].lower():
            print(f'\nEstrutura da tabela {tabela[0]}:')
            cursor.execute(f"PRAGMA table_info({tabela[0]})")
            colunas = cursor.fetchall()
            for coluna in colunas:
                print(f'  {coluna[1]} - {coluna[2]}')
    
    conn.close()
else:
    print('Banco de dados não encontrado!')
