#!/usr/bin/env python3
"""
Script para corrigir colunas faltantes no MySQL
Adiciona colunas que existem no modelo mas não no banco
"""

import pymysql
from datetime import datetime

# Configuração do MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'chat_empenhos',
    'charset': 'utf8mb4'
}

def fix_mysql_columns():
    """Adiciona colunas faltantes no MySQL"""
    connection = None
    try:
        # Conectar ao MySQL
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        print("🔧 CORRIGINDO COLUNAS NO MYSQL")
        print("=" * 40)
        
        # Lista de alterações necessárias
        alterations = [
            # Tabela empenho
            {
                'table': 'empenho',
                'column': 'valor_empenhado',
                'sql': "ALTER TABLE empenho ADD COLUMN valor_empenhado FLOAT NOT NULL DEFAULT 0.0"
            },
            # Tabela contrato  
            {
                'table': 'contrato', 
                'column': 'valor_total',
                'sql': "ALTER TABLE contrato ADD COLUMN valor_total FLOAT NOT NULL DEFAULT 0.0"
            },
            # Tabela nota_fiscal
            {
                'table': 'nota_fiscal',
                'column': 'valor_liquido', 
                'sql': "ALTER TABLE nota_fiscal ADD COLUMN valor_liquido FLOAT NOT NULL DEFAULT 0.0"
            }
        ]
        
        for alt in alterations:
            try:
                # Verificar se a coluna já existe
                cursor.execute(f"DESCRIBE {alt['table']}")
                columns = [row[0] for row in cursor.fetchall()]
                
                if alt['column'] not in columns:
                    print(f"➕ Adicionando coluna {alt['column']} em {alt['table']}")
                    cursor.execute(alt['sql'])
                    connection.commit()
                    print(f"✅ Coluna {alt['column']} adicionada com sucesso!")
                else:
                    print(f"✅ Coluna {alt['column']} já existe em {alt['table']}")
                    
            except Exception as e:
                print(f"⚠️  Erro ao adicionar {alt['column']} em {alt['table']}: {e}")
        
        # Atualizar dados onde necessário (copiar valor para valor_empenhado, etc.)
        try:
            print("\n🔄 ATUALIZANDO DADOS...")
            
            # Empenhos: copiar valor para valor_empenhado se estiver vazio
            cursor.execute("UPDATE empenho SET valor_empenhado = valor WHERE valor_empenhado = 0")
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"✅ Atualizados {rows_updated} empenhos (valor_empenhado)")
            
            # Contratos: copiar valor para valor_total se estiver vazio  
            cursor.execute("UPDATE contrato SET valor_total = valor WHERE valor_total = 0")
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"✅ Atualizados {rows_updated} contratos (valor_total)")
                
            # Notas: copiar valor para valor_liquido se estiver vazio
            cursor.execute("UPDATE nota_fiscal SET valor_liquido = valor WHERE valor_liquido = 0")
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"✅ Atualizadas {rows_updated} notas fiscais (valor_liquido)")
                
            connection.commit()
            
        except Exception as e:
            print(f"⚠️  Erro ao atualizar dados: {e}")
        
        print("\n✅ CORREÇÃO FINALIZADA!")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Erro de conexão MySQL: {e}")
        print("➡️  Verifique se o XAMPP está rodando")
        
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    fix_mysql_columns()
