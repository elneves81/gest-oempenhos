#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar as tabelas do sistema de notas fiscais
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import NotaFiscal

def criar_tabelas_notas():
    """Cria as tabelas do sistema de notas fiscais"""
    
    print("🔄 CRIAÇÃO DAS TABELAS DE NOTAS FISCAIS")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Verificar se a tabela já existe
            if db.engine.dialect.has_table(db.engine, 'notas_fiscais'):
                print("⚠️  Tabela 'notas_fiscais' já existe!")
                resposta = input("Deseja recriar a tabela? (s/N): ").strip().lower()
                if resposta == 's':
                    print("🗑️  Removendo tabela existente...")
                    db.engine.execute('DROP TABLE IF EXISTS notas_fiscais')
                else:
                    print("✅ Mantendo tabela existente.")
                    return
            
            # Criar tabela
            print("🔧 Criando tabela 'notas_fiscais'...")
            db.create_all()
            
            print("✅ Tabela 'notas_fiscais' criada com sucesso!")
            print("\n📋 Estrutura da tabela:")
            print("- id (chave primária)")
            print("- numero_nota (único)")
            print("- serie")
            print("- chave_acesso") 
            print("- empenho_id (FK)")
            print("- fornecedor_nome")
            print("- fornecedor_cnpj")
            print("- datas (emissao, vencimento, recebimento, pagamento)")
            print("- valores (bruto, desconto, impostos, liquido)")
            print("- status")
            print("- informações de pagamento")
            print("- observações")
            print("- metadados (created_at, updated_at, usuario_id)")
            
            print("\n🎉 Sistema de notas fiscais pronto para uso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    criar_tabelas_notas()
