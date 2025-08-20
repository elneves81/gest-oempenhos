#!/usr/bin/env python3
"""
Script para atualizar o banco de dados com a tabela de itens do contrato
"""

import os
import sys
import sqlite3
from datetime import datetime

def main():
    # Caminho do banco de dados
    db_path = os.path.join('instance', 'empenhos.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verificando se a tabela itens_contrato já existe...")
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='itens_contrato'
        """)
        
        if cursor.fetchone():
            print("✅ Tabela itens_contrato já existe!")
            conn.close()
            return True
        
        print("📝 Criando tabela itens_contrato...")
        
        # Criar a tabela de itens do contrato
        cursor.execute("""
            CREATE TABLE itens_contrato (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contrato_id INTEGER NOT NULL,
                lote VARCHAR(20),
                item VARCHAR(50) NOT NULL,
                descricao TEXT NOT NULL,
                marca VARCHAR(100),
                quantidade DECIMAL(10,3) NOT NULL,
                unidade VARCHAR(20) NOT NULL,
                valor_unitario DECIMAL(10,4) NOT NULL,
                valor_total DECIMAL(15,2) NOT NULL,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id) ON DELETE CASCADE
            )
        """)
        
        # Criar índices para melhorar performance
        cursor.execute("""
            CREATE INDEX idx_itens_contrato_id ON itens_contrato(contrato_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_itens_item ON itens_contrato(item)
        """)
        
        # Verificar se existem novos campos no modelo Contrato que precisam ser adicionados
        print("🔍 Verificando campos do modelo Contrato...")
        
        cursor.execute("PRAGMA table_info(contratos)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        # Campos que precisam existir (baseado no modelo atualizado)
        campos_necessarios = {
            'gestor': 'VARCHAR(200)',
            'gestor_suplente': 'VARCHAR(200)', 
            'fiscal': 'VARCHAR(200)',
            'fiscal_suplente': 'VARCHAR(200)'
        }
        
        # Adicionar campos que não existem
        for campo, tipo in campos_necessarios.items():
            if campo not in colunas_existentes:
                print(f"➕ Adicionando campo {campo}...")
                cursor.execute(f"ALTER TABLE contratos ADD COLUMN {campo} {tipo}")
        
        # Commit das alterações
        conn.commit()
        
        print("✅ Atualização do banco de dados concluída com sucesso!")
        print(f"📊 Nova tabela criada: itens_contrato")
        print(f"🔗 Relacionamento: itens_contrato.contrato_id → contratos.id")
        
        # Mostrar estrutura da nova tabela
        cursor.execute("PRAGMA table_info(itens_contrato)")
        colunas = cursor.fetchall()
        print(f"\n📋 Estrutura da tabela itens_contrato:")
        for col in colunas:
            print(f"   {col[1]} - {col[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("🚀 Iniciando atualização do banco de dados...")
    print("="*50)
    
    if main():
        print("="*50)
        print("✅ Atualização concluída!")
        sys.exit(0)
    else:
        print("="*50)
        print("❌ Falha na atualização!")
        sys.exit(1)
