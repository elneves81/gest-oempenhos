#!/usr/bin/env python3
"""
Script para adicionar novos campos à tabela de contratos
"""

import sqlite3
import os

def adicionar_campos_contrato():
    """Adiciona novos campos à tabela contratos"""
    
    # Conectar ao banco
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'empenhos.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Adicionando novos campos à tabela contratos...")
        
        # Lista de novos campos para adicionar
        novos_campos = [
            ('cnpj_fornecedor', 'VARCHAR(18)'),
            ('responsavel_nome', 'VARCHAR(200)'),
            ('responsavel_email', 'VARCHAR(200)'),
            ('responsavel_telefone', 'VARCHAR(20)'),
            ('responsavel_cargo', 'VARCHAR(100)'),
            ('arquivo_contrato', 'VARCHAR(255)')
        ]
        
        # Verificar quais campos já existem
        cursor.execute("PRAGMA table_info(contratos)")
        campos_existentes = [row[1] for row in cursor.fetchall()]
        
        campos_adicionados = 0
        
        for campo, tipo in novos_campos:
            if campo not in campos_existentes:
                try:
                    cursor.execute(f"ALTER TABLE contratos ADD COLUMN {campo} {tipo}")
                    print(f"   ✅ Campo '{campo}' adicionado")
                    campos_adicionados += 1
                except Exception as e:
                    print(f"   ❌ Erro ao adicionar campo '{campo}': {e}")
            else:
                print(f"   ℹ️  Campo '{campo}' já existe")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Migração concluída!")
        print(f"   - {campos_adicionados} novos campos adicionados")
        print(f"   - Banco atualizado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False

if __name__ == '__main__':
    print("🚀 MIGRAÇÃO DE BANCO - NOVOS CAMPOS CONTRATOS")
    print("=" * 50)
    
    if adicionar_campos_contrato():
        print("\n🎯 Migração realizada com sucesso!")
        print("\nNovos campos disponíveis:")
        print("• cnpj_fornecedor - CNPJ do fornecedor")
        print("• responsavel_nome - Nome do responsável")
        print("• responsavel_email - Email do responsável") 
        print("• responsavel_telefone - Telefone do responsável")
        print("• responsavel_cargo - Cargo do responsável")
        print("• arquivo_contrato - Nome do arquivo anexado")
    else:
        print("\n❌ Falha na migração!")
