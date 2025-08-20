#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar as colunas extras diretamente no banco de dados
"""

import sqlite3
import os

def adicionar_colunas():
    """Adiciona as colunas extras ao banco existente"""
    
    # Caminho para o banco
    db_path = os.path.join('instance', 'database.db')
    
    # Garantir que o diretório existe
    os.makedirs('instance', exist_ok=True)
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela contratos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas_existentes = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tabelas existentes: {tabelas_existentes}")
        
        if 'contratos' not in tabelas_existentes:
            print("⚠️ Tabela contratos não existe, criando estrutura básica...")
            
            # Criar tabela básica de contratos com os campos essenciais
            cursor.execute("""
            CREATE TABLE contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_pregao VARCHAR(50),
                data_pregao DATE,
                numero_contrato VARCHAR(50),
                data_contrato DATE,
                numero_ctr VARCHAR(50),
                numero_processo VARCHAR(100),
                data_processo DATE,
                digito_verificador VARCHAR(10),
                tipo_contratacao VARCHAR(50),
                objeto TEXT NOT NULL,
                resumo_objeto TEXT,
                fornecedor VARCHAR(200) NOT NULL,
                cnpj_fornecedor VARCHAR(18),
                responsavel_nome VARCHAR(200),
                responsavel_email VARCHAR(200),
                responsavel_telefone VARCHAR(20),
                responsavel_cargo VARCHAR(100),
                responsavel_emails_extras TEXT,
                responsavel_telefones_extras TEXT,
                arquivo_contrato VARCHAR(255),
                valor_total DECIMAL(15,2) NOT NULL,
                valor_inicial DECIMAL(15,2),
                data_assinatura DATE NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                data_fim_original DATE,
                gestor VARCHAR(200),
                gestor_suplente VARCHAR(200),
                fiscal VARCHAR(200),
                fiscal_suplente VARCHAR(200),
                gestor_fiscal VARCHAR(200),
                gestor_superior VARCHAR(200),
                status VARCHAR(20) DEFAULT 'ATIVO',
                modalidade_licitacao VARCHAR(50),
                lei_base VARCHAR(200),
                orgao_contratante VARCHAR(200),
                secretaria VARCHAR(200),
                tipo_garantia VARCHAR(100),
                valor_garantia DECIMAL(15,2),
                validade_garantia DATE,
                observacoes TEXT,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("✅ Tabela contratos criada com todas as colunas!")
            
        else:
            print("✅ Tabela contratos já existe")
            
            # Verificar se as colunas extras já existem
            cursor.execute("PRAGMA table_info(contratos)")
            colunas_existentes = [col[1] for col in cursor.fetchall()]
            
            # Adicionar colunas se não existirem
            colunas_para_adicionar = [
                ('responsavel_emails_extras', 'TEXT'),
                ('responsavel_telefones_extras', 'TEXT')
            ]
            
            for coluna, tipo in colunas_para_adicionar:
                if coluna not in colunas_existentes:
                    print(f"➕ Adicionando coluna: {coluna}")
                    cursor.execute(f"ALTER TABLE contratos ADD COLUMN {coluna} {tipo}")
                else:
                    print(f"✅ Coluna {coluna} já existe")
        
        # Commit das mudanças
        conn.commit()
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(contratos)")
        colunas = cursor.fetchall()
        
        print(f"\n📋 Estrutura final da tabela contratos ({len(colunas)} colunas):")
        
        colunas_responsavel = []
        for col in colunas:
            nome = col[1]
            if nome.startswith('responsavel_'):
                colunas_responsavel.append(nome)
        
        print("📧 Colunas do responsável:")
        for col in sorted(colunas_responsavel):
            print(f"  ✓ {col}")
            
        # Verificar campos específicos
        novos_campos = ['responsavel_emails_extras', 'responsavel_telefones_extras']
        print("\n🎯 Verificação dos novos campos:")
        for campo in novos_campos:
            if campo in colunas_responsavel:
                print(f"✅ Campo {campo} está presente!")
            else:
                print(f"❌ Campo {campo} NÃO encontrado!")
        
        print("\n🎉 Operação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    adicionar_colunas()
