#!/usr/bin/env python3
"""
Script para adicionar a coluna contrato_otimizado_id na tabela empenhos
"""

import sqlite3
import sys
import os

def fix_contrato_otimizado_column():
    """Adiciona a coluna contrato_otimizado_id se ela não existir"""
    
    db_path = 'empenhos.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados {db_path} não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(empenhos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("🔍 Colunas existentes na tabela empenhos:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        if 'contrato_otimizado_id' in column_names:
            print("✅ Coluna contrato_otimizado_id já existe!")
            return True
        
        print("\n📝 Adicionando coluna contrato_otimizado_id...")
        
        # Adicionar a nova coluna
        cursor.execute("""
            ALTER TABLE empenhos 
            ADD COLUMN contrato_otimizado_id INTEGER
        """)
        
        # Criar índice para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_empenhos_contrato_otimizado 
            ON empenhos(contrato_otimizado_id)
        """)
        
        conn.commit()
        print("✅ Coluna contrato_otimizado_id adicionada com sucesso!")
        
        # Verificar novamente
        cursor.execute("PRAGMA table_info(empenhos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'contrato_otimizado_id' in column_names:
            print("✅ Verificação: Coluna existe na tabela!")
            return True
        else:
            print("❌ Erro: Coluna não foi criada!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔧 Corrigindo estrutura da tabela empenhos...")
    success = fix_contrato_otimizado_column()
    
    if success:
        print("\n🎉 Correção concluída com sucesso!")
        print("Agora você pode executar o app.py novamente.")
    else:
        print("\n💥 Erro na correção!")
        sys.exit(1)
