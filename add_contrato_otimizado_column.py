#!/usr/bin/env python3
"""
Script para adicionar coluna contrato_otimizado_id à tabela empenhos
"""
import sqlite3
import os

def add_contrato_otimizado_column():
    db_path = 'empenhos.db'
    if not os.path.exists(db_path):
        print("❌ Banco empenhos.db não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(empenhos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'contrato_otimizado_id' in columns:
            print("✅ Coluna contrato_otimizado_id já existe!")
        else:
            # Adicionar a nova coluna
            cursor.execute("""
                ALTER TABLE empenhos 
                ADD COLUMN contrato_otimizado_id INTEGER 
                REFERENCES contratos_otimizados(id)
            """)
            print("✅ Coluna contrato_otimizado_id adicionada com sucesso!")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Adicionando coluna contrato_otimizado_id...")
    add_contrato_otimizado_column()
