#!/usr/bin/env python3
"""
Script para adicionar a coluna contrato_otimizado_id na tabela empenhos
"""

import sqlite3
import os

def adicionar_coluna_contrato_otimizado():
    """Adiciona a coluna contrato_otimizado_id na tabela empenhos"""
    
    db_path = 'empenhos.db'
    
    if not os.path.exists(db_path):
        print("❌ Arquivo empenhos.db não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(empenhos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("📋 Colunas atuais na tabela empenhos:")
        for col_name in column_names:
            print(f"   - {col_name}")
        
        if 'contrato_otimizado_id' in column_names:
            print("✅ Coluna contrato_otimizado_id já existe!")
            return True
        
        print("\n🔧 Adicionando coluna contrato_otimizado_id...")
        
        # Adicionar a nova coluna
        cursor.execute("""
            ALTER TABLE empenhos 
            ADD COLUMN contrato_otimizado_id INTEGER 
            REFERENCES contratos_otimizados(id)
        """)
        
        conn.commit()
        print("✅ Coluna contrato_otimizado_id adicionada com sucesso!")
        
        # Verificar novamente
        cursor.execute("PRAGMA table_info(empenhos)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("\n📋 Colunas após a alteração:")
        for col_name in column_names:
            print(f"   - {col_name}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando adição da coluna contrato_otimizado_id...")
    sucesso = adicionar_coluna_contrato_otimizado()
    
    if sucesso:
        print("\n✅ Operação concluída com sucesso!")
        print("💡 Agora você pode usar o relacionamento contrato_otimizado no modelo Empenho")
    else:
        print("\n❌ Falha na operação!")
