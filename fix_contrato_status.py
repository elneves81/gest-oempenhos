#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar a coluna 'status' na tabela 'contrato'
"""

import pymysql

def add_status_column():
    try:
        # Conexão com MySQL
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='chat_empenhos',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'chat_empenhos' 
            AND TABLE_NAME = 'contrato' 
            AND COLUMN_NAME = 'status'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if column_exists:
            print("✅ Coluna 'status' já existe na tabela 'contrato'")
        else:
            print("🔧 Adicionando coluna 'status' na tabela 'contrato'...")
            
            # Adicionar a coluna status
            cursor.execute("""
                ALTER TABLE contrato 
                ADD COLUMN status VARCHAR(20) DEFAULT 'ATIVO' AFTER empresa
            """)
            
            # Adicionar índice na coluna status
            cursor.execute("""
                ALTER TABLE contrato 
                ADD INDEX idx_contrato_status (status)
            """)
            
            # Atualizar registros existentes para ter status 'ATIVO'
            cursor.execute("""
                UPDATE contrato 
                SET status = 'ATIVO' 
                WHERE status IS NULL
            """)
            
            connection.commit()
            print("✅ Coluna 'status' adicionada com sucesso!")
            print("✅ Índice criado para a coluna 'status'")
            print("✅ Registros existentes atualizados com status 'ATIVO'")
        
        # Verificar a estrutura da tabela
        print("\n📋 Estrutura atual da tabela 'contrato':")
        cursor.execute("DESCRIBE contrato")
        columns = cursor.fetchall()
        
        for column in columns:
            field_name = column[0]
            field_type = column[1]
            null_allowed = column[2]
            key_info = column[3]
            default_value = column[4]
            extra = column[5]
            
            print(f"  {field_name}: {field_type} | NULL: {null_allowed} | Key: {key_info} | Default: {default_value}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Operação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando adição da coluna 'status' na tabela 'contrato'...")
    add_status_column()
