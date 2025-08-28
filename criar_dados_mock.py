#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar dados mock para testes do sistema
"""

import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def criar_dados_mock():
    """Cria dados de exemplo para teste"""
    
    conn = sqlite3.connect('empenhos.db')
    cursor = conn.cursor()
    
    print("🗃️ Verificando estrutura das tabelas...")
    
    # Listar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tabelas encontradas: {tabelas}")
    
    try:
        # 1. USUÁRIOS MOCK
        print("\n👥 Criando usuários mock...")
        usuarios_mock = [
            ('admin', 'admin@guarapuava.pr.gov.br', generate_password_hash('admin123'), True, True),
            ('gestor1', 'gestor1@guarapuava.pr.gov.br', generate_password_hash('123456'), True, False),
            ('gestor2', 'gestor2@guarapuava.pr.gov.br', generate_password_hash('123456'), True, False),
            ('operador1', 'operador1@guarapuava.pr.gov.br', generate_password_hash('123456'), True, False),
            ('operador2', 'operador2@guarapuava.pr.gov.br', generate_password_hash('123456'), True, False),
        ]
        
        for usuario in usuarios_mock:
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, email, password_hash, is_active, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, usuario)
        
        # 2. EMPENHOS MOCK
        print("💰 Criando empenhos mock...")
        secretarias = ['Secretaria de Saúde', 'Secretaria de Educação', 'Secretaria de Obras', 'Secretaria de Administração']
        
        for i in range(1, 21):  # 20 empenhos
            numero_empenho = f"EMP-2024-{i:04d}"
            data_empenho = datetime.now() - timedelta(days=random.randint(1, 365))
            valor = round(random.uniform(1000, 100000), 2)
            
            cursor.execute("""
                INSERT OR IGNORE INTO empenhos 
                (numero_empenho, data_empenho, valor_empenhado, resumo_objeto, objeto, fornecedores, status, numero_ctr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_empenho, 
                data_empenho.strftime('%Y-%m-%d'),
                valor,
                f"Resumo do empenho {i}",
                f"Objeto do empenho {i} para serviços municipais",
                f"Fornecedor {random.randint(1, 20)} Ltda",
                'Ativo',
                f"CTR-{i:04d}"
            ))
        
        # 3. CONTRATOS MOCK
        print("📋 Criando contratos mock...")
        for i in range(1, 16):  # 15 contratos
            numero_contrato = f"CT-2024-{i:03d}"
            data_inicio = datetime.now() - timedelta(days=random.randint(30, 300))
            data_fim = data_inicio + timedelta(days=random.randint(180, 720))
            valor = round(random.uniform(10000, 500000), 2)
            secretaria = random.choice(secretarias)
            
            cursor.execute("""
                INSERT OR IGNORE INTO contratos 
                (numero_contrato, data_inicio, data_fim, valor_total, secretaria, objeto, status, fornecedor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_contrato,
                data_inicio.strftime('%Y-%m-%d'),
                data_fim.strftime('%Y-%m-%d'),
                valor,
                secretaria,
                f"Contrato de serviços para {secretaria}",
                'Vigente',
                f"Fornecedor {random.randint(1, 30)} Ltda"
            ))
        
        # 4. MENSAGENS DE CHAT MOCK
        print("💬 Criando mensagens de chat mock...")
        if 'chat_messages' in tabelas:
            mensagens_exemplo = [
                ("Olá! Como posso ajudar com os empenhos?", "Olá! Posso ajudar com consultas sobre empenhos, contratos e relatórios."),
                ("Preciso verificar o status do empenho EMP-2024-0001", "O empenho EMP-2024-0001 está com status Ativo e valor de R$ 15.450,00."),
                ("Qual o valor total empenhado este mês?", "O valor total empenhado este mês é de R$ 1.250.890,45."),
                ("Como faço para consultar contratos vigentes?", "Acesse o menu Contratos e use o filtro 'Status: Vigente' para ver todos os contratos ativos."),
                ("Existe algum empenho em atraso?", "Sim, há 3 empenhos com vencimento em atraso. Deseja ver a lista?"),
            ]
            
            session_id = "session_demo_001"
            for i, (mensagem, resposta) in enumerate(mensagens_exemplo):
                # Mensagem do usuário
                cursor.execute("""
                    INSERT OR IGNORE INTO chat_messages 
                    (user_id, message, timestamp, session_id)
                    VALUES (?, ?, ?, ?)
                """, (
                    1,  # user admin
                    mensagem,
                    (datetime.now() - timedelta(hours=24-i*2)).isoformat(),
                    session_id
                ))
                
                # Resposta da IA
                cursor.execute("""
                    INSERT OR IGNORE INTO chat_messages 
                    (user_id, message, response, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    1,  # user admin
                    mensagem,
                    resposta,
                    (datetime.now() - timedelta(hours=24-i*2-0.1)).isoformat(),
                    session_id
                ))
        
        # 5. NOTAS FISCAIS MOCK
        print("🧾 Criando notas fiscais mock...")
        if 'notas_fiscais' in tabelas:
            for i in range(1, 31):  # 30 notas fiscais
                numero_nota = f"NF-{random.randint(1000, 9999)}"
                data_emissao = datetime.now() - timedelta(days=random.randint(1, 180))
                valor_bruto = round(random.uniform(500, 50000), 2)
                valor_liquido = round(valor_bruto * 0.92, 2)  # desconto de impostos
                
                cursor.execute("""
                    INSERT OR IGNORE INTO notas_fiscais 
                    (numero_nota, empenho_id, fornecedor_nome, fornecedor_cnpj, data_emissao, 
                     valor_bruto, valor_liquido, status, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    numero_nota,
                    random.randint(1, 20),  # empenho_id aleatório
                    f"Fornecedor {random.randint(1, 50)} Ltda",
                    f"{random.randint(10000000, 99999999):08d}0001{random.randint(10, 99)}",
                    data_emissao.strftime('%Y-%m-%d'),
                    valor_bruto,
                    valor_liquido,
                    random.choice(['Pendente', 'Aprovada', 'Paga']),
                    1  # usuario admin
                ))
        
        conn.commit()
        print("\n✅ Dados mock criados com sucesso!")
        
        # Mostrar resumo
        print("\n📊 RESUMO DOS DADOS CRIADOS:")
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"👥 Usuários: {cursor.fetchone()[0]}")
        
        if 'empenhos' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM empenhos")
            print(f"💰 Empenhos: {cursor.fetchone()[0]}")
        
        if 'contratos' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM contratos")
            print(f"📋 Contratos: {cursor.fetchone()[0]}")
        
        if 'chat_messages' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM chat_messages")
            print(f"💬 Mensagens de Chat: {cursor.fetchone()[0]}")
        
        if 'notas_fiscais' in tabelas:
            cursor.execute("SELECT COUNT(*) FROM notas_fiscais")
            print(f"🧾 Notas Fiscais: {cursor.fetchone()[0]}")
    
    except Exception as e:
        print(f"❌ Erro ao criar dados mock: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    criar_dados_mock()
